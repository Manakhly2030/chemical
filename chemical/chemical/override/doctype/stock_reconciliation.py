from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import StockReconciliation as _StockReconciliation
from chemical.chemical.override.utils import make_batches

class StockReconciliation(_StockReconciliation):
    def make_batches(self, warehouse_field):
        return make_batches(self, warehouse_field)