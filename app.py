from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import json
from markupsafe import escape
import os
import pika
import requests
import sys
import time

from db import PaymentDatabase, PromoDatabase


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
promo_db = PromoDatabase()

# Payment routes
@app.route("/", methods=["POST"])
def create_payment() :
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
    try :
        result = [payment.serialize() for payment in payment_db.get_all()]
        response = jsonify({
            "result": result
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/ongoing/<email>", methods=["GET"])
def get_ongoing_payments(email) :
    try :
        email = escape(email)
        result = [payment.serialize() for payment in payment_db.get_ongoing(email)]
        response = jsonify({
            "result": result
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/history/<email>", methods=["GET"])
def get_history_payments(email) :
    try :
        email = escape(email)
        result = [payment.serialize() for payment in payment_db.get_history(email)]
        response = jsonify({
            "result": result
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/validate", methods=["POST"])
def validate_payment() :
    try :
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
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/update-payment-status", methods=["PUT"])
def update_payment_status() :
    try :
        data = request.get_json(force=True)
        invoice_number = data["invoice_number"]
        email = data["email"]
        result = data["result"]
        if result :
            payment_db.update_payment_status(invoice_number, "COMPLETED")
            if "BK" in invoice_number :
                payment_db.update_payment_booking_status(invoice_number, "paid")
                requests.post(
                    f"{booking_service_url}/pay/{invoice_number}"
                )
            elif "MB" in invoice_number :
                requests.put(
                    f"{account_service_url}/update-status-membership/",
                    data=json.dumps({
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
    except Exception as e :
        print(e.with_traceback())
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/apply-promo", methods=["POST"])
def apply_promo() :
    try :
        data = request.get_json()
        invoice_number = data["invoice_number"]
        promo_id = data["promo_id"]
        if "MB" in invoice_number :
            response = jsonify({
                "message": f"Error⛔! Promo is only available for booking payments!",
            })
            response.status_code = 400
            return response
        payment = payment_db.get_by_invoice_number(invoice_number)
        if payment is None :
            response = jsonify({
                "message": f"Error⛔! Payment with invoice number {payment.invoice_number} is not found!"
            })
            response.status_code = 400
            return response
        promo = promo_db.get_by_id(promo_id)
        if promo is None :
            response = jsonify({
                "message": f"Error⛔! Promo with id {promo_id} is not found!"
            })
            response.status_code = 400
            return response
        payment_db.update_promo(invoice_number, promo.serialize())
        return Response(status=204)
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response    

# Promo routes
@app.route("/promo", methods=["POST"])
def create_promo() :
    data = request.get_json()
    try :
        promo = promo_db.create(data)
        response = jsonify({
            "message": f"New promo with id {promo.id} successfully created!👍😀"
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/promo", methods=["GET"])
def get_all_promos() :
    try :
        result = [promo.serialize() for promo in promo_db.get_all()]
        response = jsonify({
            "result": result
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/promo/<id>", methods=["GET"])
def get_promo_by_id(id) :
    try :
        id = int(id)
        result = promo_db.get_by_id(id)
        response = jsonify({
            "result": result
        })
        response.status_code = 200
        return response
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.route("/promo/<id>", methods=["DELETE"])
def delete_promo_by_id() :
    try :
        id = int(id)
        promo_db.delete_by_id(id)
        return Response(status=204)
    except Exception as e :
        response = jsonify({
            "message": f"Exception occurred⛔! Exception: {e}"
        })
        response.status_code = 500
        return response

@app.after_request 
def after_request_callback(response): 
    sys.stdout.flush()
    return response

if __name__ == "__main__" :
    app.run(debug=True, host="0.0.0.0")