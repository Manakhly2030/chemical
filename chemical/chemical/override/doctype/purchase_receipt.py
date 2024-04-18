from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt as _PurchaseReceipt
from chemical.chemical.override.utils import make_batches

class PurchaseReceipt(_PurchaseReceipt):
    def make_batches(self, warehouse_field):
        return make_batches(self, warehouse_field)