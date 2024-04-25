from erpnext.subcontracting.doctype.subcontracting_receipt.subcontracting_receipt import SubcontractingReceipt as _SubcontractingReceipt
from chemical.chemical.override.utils import make_batches

class SubcontractingReceipt(_SubcontractingReceipt):
    def make_batches(self, warehouse_field):
        return make_batches(self, warehouse_field)