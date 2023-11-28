from abc import ABC
from enum import Enum
from .payment_method import PaymentMethod
from .promo import Promo

class Payment(ABC) :
    class PaymentStatus(Enum) :
        PENDING = 0
        COMPLETED = 1
        FAILED = 2
    def __init__(self, invoice_number, total_price, payment_method:PaymentMethod, status=None) :
        self._invoice_number = invoice_number
        self._total_price = total_price
        self._payment_method = payment_method
        if status is None :
            self._status = Payment.PaymentStatus.PENDING
        elif isinstance(status, str) :
            self._status = Payment.PaymentStatus[status]
        elif isinstance(status, int) :
            self._status = Payment.PaymentStatus(status)
    # Getter(s) and setter(s)
    @property
    def invoice_number(self) :
        return self._invoice_number
    @property
    def total_price(self) :
        return self._total_price
    @property
    def payment_method(self) :
        return self._payment_method
    @property
    def status(self) :
        return self._status
    @invoice_number.setter
    def invoice_number(self, invoice_number) :
        self._invoice_number = invoice_number
    @total_price.setter
    def total_price(self, total_price) :
        self._total_price = total_price
    @payment_method.setter
    def payment_method(self, payment_method:PaymentMethod) :
        self._payment_method = payment_method
    @status.setter
    def status(self, status) :
        if status is None :
            self._status = Payment.PaymentStatus.PENDING
        elif isinstance(status, str) :
            self._status = Payment.PaymentStatus[status]
        elif isinstance(status, int) :
            self._status = Payment.PaymentStatus(status)
    # Methods
    def pay(self) -> bool :
        print("Validating payment..")
        payment_validation = self._payment_method.validate_payment()
        print(f"Payment validation: {payment_validation}")
        if payment_validation :
            self._status = "COMPLETED"
            print(f"Payment with invoice number {self._invoice_number} is completed!")
        else :
            self._status = "FAILED"
            print(f"Payment with invoice number {self._invoice_number} is failed.")
        return payment_validation
    def __str__(self) -> str:
        return (
            f"Invoice number: {self._invoice_number}\n"
            f"Payment method: {self._payment_method}\n"
        )
    def serialize(self) :
        result = {
            key.strip('_'): value for key, value in vars(self).items() if key not in ["payment_method", "promo", "status"]
        }
        result["payment_method"] = self.payment_method.serialize()
        result["status"] = self.status.name
        return result
class BookingPayment(Payment) :
    def __init__(self, invoice_number, total_price, payment_method: PaymentMethod, booking, promo:Promo=None, status=None):
        super().__init__(invoice_number, total_price, payment_method, status)
        self._booking = booking
        self._promo = promo
    # Getter(s) and setter(s)
    @property
    def booking(self) :
        return self._booking
    @property
    def promo(self) :
        return self._promo
    @booking.setter
    def booking(self, booking) :
        self._booking = booking
    @promo.setter
    def promo(self, promo:Promo) :
        if promo is not None and promo.is_valid(self._total_price) :
            discounted_total_price = min(self._booking.total_price * (1-promo.discount), promo.max_discount)
            self._total_price = discounted_total_price
            self._promo = promo
    # Methods
    def remove_promo(self) :
        if self._promo is not None :
            self._total_price = self._booking.total_price
        self._promo = None
    def pay(self) -> bool :
        if super().pay() :
            self._booking.set_status("paid")
            return True
        else :
            self._booking.cancel()
            return False
    def __str__(self) -> str:
        return (
            f"{super().__str__()}"
            f"Booking info:\n"
            f"\tFilm: {self._booking.get_tickets()[0].get_schedule().get_film().get_name()}\n"
            f"\tStudio: {self._booking.get_tickets()[0].get_schedule().get_studio().get_name()}\n"
            f"\tSeats: {', '.join([ticket.get_seat() for ticket in self._booking.get_tickets()])}\n"
            f"\tFnBs: {', '.join([str(fnb.get_name()) for fnb in self._booking.get_fnbs()]) if len(self._booking.get_fnbs())>0 else 'No FnBs'}\n"
            f"\tTotal price: {self._booking.get_total_price()}\n"
            f"Final price (net): {self._total_price}\n"
            f"Payment status: {self._status.name}\n"
        )
    def serialize(self) :
        result = {
            key.strip('_'): value for key, value in vars(self).items() if key not in ["payment_method", "promo", "status"]
        }
        result["payment_method"] = self.payment_method.serialize()
        result["promo"] = self.promo.serialize()
        result["status"] = self.status.name
        return result
class MembershipPayment(Payment) :
    def __init__(self, invoice_number, total_price, payment_method: PaymentMethod, user, status=None):
        super().__init__(invoice_number, total_price, payment_method, status)
        self._user = user
    # Getter(s) and setter(s)
    @property
    def user(self) :
        return self._user
    @user.setter
    def user(self, user) :
        self._user = user
    # Methods
    def pay(self) -> bool :
        print("Checking user status..")
        user_status_validation = self._user.check_status()
        print(f"User status validation: {user_status_validation}")
        if user_status_validation :
            return super().pay()
        else :
            self._status = "FAILED"
            print(f"Payment with invoice number {self._invoice_number} is failed.")
            return False
    def __str__(self) -> str:
        return (
            f"{super().__str__()}"
            f"User info: {self._user}\n"
            f"Final price (net): {self._total_price}\n"
            f"Payment status: {self._status.name}"
        )