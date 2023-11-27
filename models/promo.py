class Promo :
    # Class-level attribute to keep track all promos that are created
    promos = []

    def __init__(self, name:str, discount:float, max_discount:int, info:str='', min_purchase:int=0) :
        self._name = name
        self._info = info
        self._min_purchase = min_purchase
        self._discount = discount
        self._max_discount = max_discount
        # Add created promo object to class-level promos attribute
        Promo.promos.append(self)
    # Getter(s) and setter(s)
    @property
    def name(self) :
        return self._name
    @property
    def info(self) :
        return self._info
    @property
    def min_purchase(self) :
        return self._min_purchase
    @property
    def discount(self) :
        return self._discount
    @property
    def max_discount(self) :
        return self._max_discount
    @name.setter
    def name(self, name) :
        self._name = name
    @info.setter
    def info(self, info) :
        self._info = info
    @min_purchase.setter
    def min_purchase(self, min_purchase) :
        self._min_purchase = min_purchase
    @discount.setter
    def discount(self, discount) :
        self._discount = discount
    @max_discount.setter
    def max_discount(self, max_discount) :
        self._max_discount = max_discount
    # Methods
    def delete_promo(self) :
        if self in Promo.promos :
            Promo.promos.remove(self)
        del self
    def is_valid(self, amount) :
        return amount >= self.min_purchase