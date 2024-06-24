import frappe
from erpnext.stock.utils import get_stock_balance, get_incoming_rate
from erpnext.stock.doctype.batch.batch import get_batch_qty

def on_submit(self, method):
	update_valuation_rate_for_batch_no(self)

def on_cancel(self, method):
	update_valuation_rate_for_batch_no(self)

def update_valuation_rate_for_batch_no(self):
	for row in self.items:
		if not row.batch_no: continue

		valuation_rate = row.valuation_rate if self.docstatus == 1 else row.current_valuation_rate
		if valuation_rate is None:
			continue

		frappe.db.set_value("Batch", row.batch_no, 'valuation_rate', valuation_rate)

@frappe.whitelist()
def get_stock_balance_for(item_code, warehouse,
	posting_date, posting_time, batch_no=None, with_valuation_rate= True):
	frappe.has_permission("Stock Reconciliation", "write", throw = True)
	item_dict = frappe.db.get_value("Item", item_code,
		["has_serial_no", "has_batch_no"], as_dict=1)

	if not item_dict:
		# In cases of data upload to Items table
		msg = _("Item {} does not exist.").format(item_code)
		frappe.throw(msg, title=_("Missing"))

	serial_nos = ""
	with_serial_no = True if item_dict.get("has_serial_no") else False
	data = get_stock_balance(item_code, warehouse, posting_date, posting_time,
		with_valuation_rate=with_valuation_rate, with_serial_no=with_serial_no)

	if with_serial_no:
		qty, rate, serial_nos = data
	else:
		qty, rate = data

	if item_dict.get("has_batch_no"):
		qty = get_batch_qty(batch_no, warehouse, posting_date=posting_date, posting_time=posting_time) or 0
		rate = get_incoming_rate({
				"item_code": item_code,
				"warehouse": warehouse,
				"posting_date": posting_date,
				"posting_time": posting_time,
				"batch_no": batch_no
			}, raise_error_if_no_rate=True)

	return {
		'qty': qty,
		'rate': rate,
		'serial_nos': serial_nos
	}