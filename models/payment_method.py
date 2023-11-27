from abc import ABC, abstractmethod
from enum import Enum
import random

class PaymentMethod(ABC) :
    def __init__(self, invoice_number) -> None :
        self._invoice_number = invoice_number
    # Getter(s) and setter(s)
    @property
    def invoice_number(self) :
        return self._invoice_number
    @invoice_number.setter
    def invoice_number(self, invoice_number) :
        self._invoice_number = invoice_number
    def serialize(self) :
        return {
            "invoice_number": self.invoice_number,
        }
    @abstractmethod
    def validate_payment(self) :
        pass

class EWallet(PaymentMethod, ABC) :
    class WalletName(Enum) :
        GOPAY = 0
        OVO = 1
    def __init__(self, invoice_number, wallet_name) :
        super().__init__(invoice_number)
        self._wallet_name = EWallet.WalletName[wallet_name]
    # Getter(s) and setter(s)
    @property
    def wallet_name(self) :
        return self._wallet_name
    @wallet_name.setter
    def wallet_name(self, wallet_name) :
        self._wallet_name = EWallet.WalletName[wallet_name]
    def serialize(self) :
        return {
            "invoice_number": self.invoice_number,
            "wallet_name": EWallet.WalletName(self.wallet_name).name
        }
    @abstractmethod
    def validate_payment(self):
        pass
    def __str__(self) -> str:
        return f"E-Wallet ({self._wallet_name.name})"
class EWalletGoPay(EWallet) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "GOPAY")
    def validate_payment(self):
        return random.choice([False, True])
class EWalletOVO(EWallet) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "OVO")
    def validate_payment(self):
        return random.choice([False, True])

class CreditCard(PaymentMethod, ABC) :
    class CardProvider(Enum) :
        MASTERCARD = 0
        VISA = 1
    def __init__(self, invoice_number, card_provider) :
        super().__init__(invoice_number)
        self._card_provider = CreditCard.CardProvider[card_provider]
    # Getter(s) and setter(s)
    @property
    def card_provider(self) :
        return self._card_provider
    @card_provider.setter
    def card_provider(self, card_provider) :
        self._card_provider = CreditCard.CardProvider[card_provider]
    def serialize(self) :
        return {
            "invoice_number": self.invoice_number,
            "card_provider": CreditCard.CardProvider(self.card_provider).name
        }
    @abstractmethod
    def validate_payment(self):
        pass
    def __str__(self) -> str:
        return f"Credit Card ({self._card_provider.name})"
class CreditCardMastercard(CreditCard) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "MASTERCARD")
    def validate_payment(self):
        return random.choice([False, True])
class CreditCardVISA(CreditCard) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "VISA")
    def validate_payment(self):
        return random.choice([False, True])

class BankTransfer(PaymentMethod, ABC) :
    class Bank(Enum) :
        BCA = 0
        BNI = 1
        BRI = 2
    def __init__(self, invoice_number, bank) :
        super().__init__(invoice_number)
        self._bank = BankTransfer.Bank[bank]
    # Getter(s) and setter(s)
    @property
    def bank(self) :
        return self._bank
    @bank.setter
    def set_bank(self, bank) :
        self._bank = BankTransfer.Bank[bank]
    def serialize(self) :
        return {
            "invoice_number": self.invoice_number,
            "bank": BankTransfer.Bank(self.bank).name
        }
    @abstractmethod
    def validate_payment(self):
        pass
    def __str__(self) -> str:
        return f"Bank Transfer ({self._bank.name})"
class BankTransferBCA(BankTransfer) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "BCA")
    def validate_payment(self):
        return random.choice([False, True])
class BankTransferBNI(BankTransfer) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "BNI")
    def validate_payment(self):
        return random.choice([False, True])
class BankTransferBRI(BankTransfer) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number, "BRI")
    def validate_payment(self):
        return random.choice([False, True])

class QRIS(PaymentMethod) :
    def __init__(self, invoice_number) :
        super().__init__(invoice_number)
    def validate_payment(self):
        return random.choice([False, True])
    def __str__(self) -> str:
        return "QRIS"