import frappe
from frappe import msgprint, _

def dn_on_submit(self, method):
	update_sales_invoice(self)
	validate_customer_batch(self)

def update_sales_invoice(self):
	for row in self.items:
		if row.against_sales_invoice and row.si_detail:
			if self._action == 'submit':
				delivery_note = self.name
				dn_detail = row.name

			elif self._action == 'cancel':
				delivery_note = ''
				dn_detail = ''

			frappe.db.sql("""update `tabSales Invoice Item` 
				set dn_detail = %s, delivery_note = %s 
				where name = %s """, (dn_detail, delivery_note, row.si_detail))

def validate_customer_batch(self):
	for row in self.items:
		if row.batch_no:
			batch_customer = frappe.db.get_value("Batch",row.batch_no,"customer")
			if batch_customer:
				if batch_customer != self.customer:
					frappe.throw(_("Please select correct batch for customer <strong>{}</strong> in row {}".format(self.customer,row.idx)))

