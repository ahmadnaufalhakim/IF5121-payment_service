from dotenv import load_dotenv
from flask import Flask, request, jsonify
import json
from markupsafe import escape
import os
import pika
import requests
import sys
from threading import Thread
import time

from db import PaymentDatabase


app = Flask(__name__)
load_dotenv()

# External URLs
account_service_url = os.environ.get("ACCOUNT_SERVICE_URL")
booking_service_url = os.environ.get("BOOKING_SERVICE_URL")

time.sleep(5)
# RabbitMQ connections
## RabbitMQ connection parameters
rabbitmq_params = pika.ConnectionParameters(host="rabbitmq", port=5672)
connection = pika.BlockingConnection(rabbitmq_params)
channel = connection.channel()
# Declare a queue for payment creation
channel.queue_declare(queue="payment_creation_queue")
## Declare a queue for payment validation requests
channel.queue_declare(queue="payment_validation_queue")

# Database connection
payment_db = PaymentDatabase()

@app.route("/", methods=["POST"])
def create() :
    data = request.get_json()
    payments = payment_db.get_all()
    try :
        for payment in payments :
            if data["invoice_number"] == payment.invoice_number :
                response = jsonify({
                    "message": f"Error⛔! Payment with invoice number {payment.invoice_number} already exists!",
                })
                response.status_code = 400
                return response

        payment_db.create(data)
        json_message = jsonify(data).get_data(as_text=True)
        # Publish the payment validation request to RabbitMQ
        channel.basic_publish(
            exchange='',
            routing_key="payment_creation_queue",
            body=json_message
        )
        response = jsonify({
            "message": f"New payment with invoice number {data['invoice_number']} successfully created!👍😀",
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/", methods=["GET"])
def get_all_payments() :
    result = [payment.serialize() for payment in payment_db.get_all()]
    response = jsonify({
        "result": result
    })
    response.status_code = 200
    return response

@app.route("/ongoing/<email>", methods=["GET"])
def get_ongoing_payments(email) :
    email = escape(email)
    result = [payment.serialize() for payment in payment_db.get_ongoing(email)]
    response = jsonify({
        "result": result
    })
    response.status_code = 200
    return response

@app.route("/history/<email>", methods=["GET"])
def get_history_payments(email) :
    email = escape(email)
    result = [payment.serialize() for payment in payment_db.get_history(email)]
    response = jsonify({
        "result": result
    })
    response.status_code = 200
    return response

@app.route("/validate", methods=["POST"])
def validate_payment() :
    data = request.get_json()
    message_body = {
        "invoice_number": data["invoice_number"],
    }
    json_message = jsonify(message_body).get_data(as_text=True)
    # Publish the payment validation request to RabbitMQ
    channel.basic_publish(
        exchange='',
        routing_key="payment_validation_queue",
        body=json_message
    )
    return "Payment validation request sent to RabbitMQ."

@app.route("/update-payment-status", methods=["PUT"])
def update_payment_status() :
    data = json.loads(request.get_json())
    invoice_number = data["invoice_number"]
    email = data["email"]
    result = data["result"]
    if result :
        payment_db.update_payment_status(invoice_number, "COMPLETED")
        if "BK" in invoice_number :
            payment_db.update_payment_booking_status(invoice_number, "paid")
        elif "MB" in invoice_number :
            requests.put(
                f"{account_service_url}/update-status-membership/",
                data=jsonify({
                    "email": email,
                    "status": result
                })
            )
    else :
        payment_db.update_payment_status(invoice_number, "FAILED")
        if "BK" in invoice_number :
            payment_db.update_payment_booking_status(invoice_number, "canceled")
            requests.post(
                f"{booking_service_url}/cancel/{invoice_number}"
            )

@app.after_request 
def after_request_callback(response): 
    sys.stdout.flush()
    return response

if __name__ == "__main__" :
    app.run(debug=True, host="0.0.0.0")