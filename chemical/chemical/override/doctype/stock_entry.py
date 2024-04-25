from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as _StockEntry
from chemical.chemical.override.utils import make_batches


class StockEntry(_StockEntry):
	def make_batches(self, warehouse_field):
		return make_batches(self, warehouse_field)