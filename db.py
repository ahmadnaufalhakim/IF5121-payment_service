from models import Payment, BookingPayment, MembershipPayment
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
from models import Promo

class PaymentDatabase :
    def __init__(self) -> None:
        # Maps payment invoice number to payment object
        self.booking_payments = {}
        self.membership_payments = {}

    def create(self, payment:dict) :
        if "BankTransfer" in payment["payment_method"] :
            if "BCA" in payment["payment_method"] :
                payment_method = BankTransferBCA(payment["invoice_number"])
            elif "BNI" in payment["payment_method"] :
                payment_method = BankTransferBNI(payment["invoice_number"])
            elif "BRI" in payment["payment_method"] :
                payment_method = BankTransferBRI(payment["invoice_number"])
        elif "CreditCard" in payment["payment_method"] :
            if "Mastercard" in payment["payment_method"] :
                payment_method = CreditCardMastercard(payment["invoice_number"])
            elif "BNI" in payment["payment_method"] :
                payment_method = CreditCardVISA(payment["invoice_number"])
        elif "EWallet" in payment["payment_method"] :
            if "GoPay" in payment["payment_method"] :
                payment_method = EWalletGoPay(payment["invoice_number"])
            elif "OVO" in payment["payment_method"] :
                payment_method = EWalletOVO(payment["invoice_number"])
        elif payment["payment_method"] == "QRIS" :
            payment_method = QRIS(payment["invoice_number"])

        if "user" in payment :
            self.membership_payments[payment["invoice_number"]] = MembershipPayment(
                payment["invoice_number"],
                payment["total_price"],
                payment_method,
                payment["user"],
                status=None
            )
        elif "booking" in payment :
            self.booking_payments[payment["invoice_number"]] = BookingPayment(
                payment["invoice_number"],
                payment["total_price"],
                payment_method,
                payment["booking"],
                payment["promo"],
                status=None
            )
        return

    def get_all(self) :
        result = [value for _, value in self.booking_payments.items()]
        result.extend([value for _, value in self.membership_payments.items()])
        return result

    def get_by_invoice_number(self, invoice_number) :
        if "BK" in invoice_number :
            return self.booking_payments[invoice_number]
        elif "MB" in invoice_number :
            return self.membership_payments[invoice_number]

    def get_ongoing(self, email) :
        result = []
        for invoice_number in self.booking_payments :
            if self.booking_payments[invoice_number].status == Payment.PaymentStatus.PENDING and self.booking_payments[invoice_number].booking["user"]["email"] == email :
                result.append(self.booking_payments[invoice_number])
        for invoice_number in self.membership_payments :
            if self.membership_payments[invoice_number].status == Payment.PaymentStatus.PENDING and self.membership_payments[invoice_number].user["email"] == email :
                result.append(self.membership_payments[invoice_number])
        return result

    def get_history(self, email) :
        result = []
        for invoice_number in self.booking_payments :
            if self.booking_payments[invoice_number].status != Payment.PaymentStatus.PENDING and self.booking_payments[invoice_number].booking["user"]["email"] == email :
                result.append(self.booking_payments[invoice_number])
        for invoice_number in self.membership_payments :
            if self.membership_payments[invoice_number].status != Payment.PaymentStatus.PENDING and self.membership_payments[invoice_number].user["email"] == email :
                result.append(self.membership_payments[invoice_number])
        return result

    def update_payment_status(self, invoice_number, status) :
        if "BK" in invoice_number :
            self.booking_payments[invoice_number].status = status
        elif "MB" in invoice_number :
            self.membership_payments[invoice_number].status = status
        return

    def update_payment_booking_status(self, invoice_number, status) :
        self.booking_payments[invoice_number].booking["status"] = status
        return

    def delete_by_invoice_number(self, invoice_number) :
        if "BK" in invoice_number and invoice_number in self.booking_payments :
            del self.booking_payments[invoice_number]
        elif "MB" in invoice_number and invoice_number in self.membership_payments :
            del self.membership_payments[invoice_number]
        return

class PromoDatabase :
    promo_id_counter = 1
    def __init__(self) -> None:
        self.promos = {}

    def create(self, promo:dict) :
        promo_id = PromoDatabase.promo_id_counter
        PromoDatabase.promo_id_counter += 1
        if "info" not in promo :
            promo["info"] = ''
        if "min_purchase" not in promo :
            promo["min_purchase"] = 0
        self.promos[promo_id] = Promo(
            promo_id,
            promo["name"],
            promo["discount"],
            promo["max_discount"],
            promo["info"],
            promo["min_purchase"]
        )
        return self.promos[promo_id]

    def get_all(self) :
        result = [value for _, value in self.promos.items()]
        return result

    def get_by_id(self, id) :
        result = self.promos[id]
        return result

    def delete_by_id(self, id) :
        if id in self.promos: del self.promos[id]
        return