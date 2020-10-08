import frappe
from frappe import msgprint, _
from frappe.utils import nowdate, flt

def sl_before_submit(self, method):
	batch_qty_validation_with_date_time(self)
	
def batch_qty_validation_with_date_time(self):
	if self.batch_no and not self.get("allow_negative_stock"):
		batch_bal_after_transaction = flt(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and batch_no=%s and concat(posting_date, ' ', posting_time) <= %s %s """,
			(self.warehouse, self.item_code, self.batch_no, self.posting_date, self.posting_time))[0][0])
	
		if flt(batch_bal_after_transaction) < 0:
			frappe.throw(_("Stock balance in Batch {0} will become negative {1} for Item {2} at Warehouse {3} at date {4} and time {5}")
				.format(self.batch_no, batch_bal_after_transaction, self.item_code, self.warehouse, self.posting_date, self.posting_time))
