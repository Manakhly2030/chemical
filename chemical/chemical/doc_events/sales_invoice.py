import frappe
from frappe import msgprint, _

def before_insert(self, method):
	if not self.name and self.is_opening == "Yes":
		self.naming_series = 'O' + self.naming_series

def si_before_submit(self,method):
	validate_customer_batch(self)
	
def validate_customer_batch(self):
	for row in self.items:
		if row.batch_no:
			batch_customer = frappe.db.get_value("Batch",row.batch_no,"customer")
			if batch_customer:
				if batch_customer != self.customer:
					frappe.throw(_("Please select correct batch for customer <strong>{}</strong> in row {}".format(self.customer,row.idx)))
