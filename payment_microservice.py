from dotenv import load_dotenv
import pika
import json
import os
import requests
import time

from models import BookingPayment, MembershipPayment
from models import (
    BankTransferBCA,
    BankTransferBNI,
    BankTransferBRI,
    CreditCardMastercard,
    CreditCardVISA,
    EWalletGoPay,
    EWalletOVO,
    QRIS
)

load_dotenv()

# In-memory temporary "database"
booking_payments = {}
membership_payments = {}

# External URLs
payment_service_url = os.environ.get("PAYMENT_SERVICE_URL")

time.sleep(5)
# RabbitMQ connections
# RabbitMQ connection parameters
rabbitmq_params = pika.ConnectionParameters(host="rabbitmq", port=5672)
connection = pika.BlockingConnection(rabbitmq_params)
channel = connection.channel()
# Declare a queue for payment creation
channel.queue_declare(queue="payment_creation_queue")
# Declare a queue for payment validation requests
channel.queue_declare(queue="payment_validation_queue")

def callback_creation(ch, method, properties, body) :
    message_body = json.loads(body.decode())
    # Insert to temp in-memory "database"
    if "BankTransfer" in message_body["payment_method"] :
        if "BCA" in message_body["payment_method"] :
            payment_method = BankTransferBCA(message_body["invoice_number"])
        elif "BNI" in message_body["payment_method"] :
            payment_method = BankTransferBNI(message_body["invoice_number"])
        elif "BRI" in message_body["payment_method"] :
            payment_method = BankTransferBRI(message_body["invoice_number"])
    elif "CreditCard" in message_body["payment_method"] :
        if "Mastercard" in message_body["payment_method"] :
            payment_method = CreditCardMastercard(message_body["invoice_number"])
        elif "BNI" in message_body["payment_method"] :
            payment_method = CreditCardVISA(message_body["invoice_number"])
    elif "EWallet" in message_body["payment_method"] :
        if "GoPay" in message_body["payment_method"] :
            payment_method = EWalletGoPay(message_body["invoice_number"])
        elif "OVO" in message_body["payment_method"] :
            payment_method = EWalletOVO(message_body["invoice_number"])
    elif message_body["payment_method"] == "QRIS" :
        payment_method = QRIS(message_body["invoice_number"])
    if "user" in message_body :
        membership_payments[message_body["invoice_number"]] = MembershipPayment(
            message_body["invoice_number"],
            message_body["total_price"],
            payment_method,
            message_body["user"],
            status=None
        )
    elif "booking" in message_body :
        booking_payments[message_body["invoice_number"]] = BookingPayment(
            message_body["invoice_number"],
            message_body["total_price"],
            payment_method,
            message_body["booking"],
            message_body["promo"],
            status=None
        )
    print(f"Payment with invoice number {message_body['invoice_number']} created in internal mem")

def callback_validation(ch, method, properties, body) :
    # Deserialize the JSON message
    message_body = json.loads(body.decode())

    invoice_number = message_body["invoice_number"]
    if "BK" in invoice_number :
        try :
            payment = booking_payments[invoice_number]
        except KeyError :
            return
        email = payment.booking["user"]["email"]
        del booking_payments[invoice_number]
    elif "MB" in invoice_number :
        try :
            payment = membership_payments[invoice_number]
        except KeyError :
            return
        email = payment.user["email"]
        del membership_payments[invoice_number]
    payment_method = payment.payment_method

    # Use the instantiated payment method to validate the payment
    result = payment_method.validate_payment()
    requests.put(
        f"{payment_service_url}/update-payment-status",
        data=json.dumps({
            "invoice_number": invoice_number,
            "email": email,
            "result": result
        })
    )
    print(f"Payment result ({result}) for invoice {invoice_number} sent back to payment (/update-payment-status)")

print("Payment microservice is waiting for incoming messages. To exit press CTRL+C")
channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue='payment_creation_queue',
    on_message_callback=callback_creation,
    auto_ack=True
)
channel.basic_consume(
    queue='payment_validation_queue',
    on_message_callback=callback_validation,
    auto_ack=True
)
channel.start_consuming()