from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice as _PurchaseInvoice
from chemical.chemical.override.utils import make_batches


class PurchaseInvoice(_PurchaseInvoice):
    def make_batches(self, warehouse_field):
        return make_batches(self, warehouse_field)