from erpnext.stock.doctype.item.item import Item
import frappe
from frappe.utils import cstr

def item_validate(self, method):
	fill_customer_code(self)
	no_change(self)


def fill_customer_code(self):
	""" Append all the customer codes and insert into "customer_code" field of item table """
	cust_code = []
	for d in self.get('customer_items'):
		cust_code.append(d.ref_code)
	self.customer_code = ""
	self.item_customer_code = ','.join(cust_code)

def validate(self, method):
	no_change(self)

def no_change(self):
	if not self.get("__islocal"):
		field = "maintain_as_is_stock"

		values = frappe.db.get_value("Item", self.name, field, as_dict=True)
	
		if cstr(self.get(field)) != cstr(values.get(field)):
			
			if self.check_if_linked_document_exists(field):
				frappe.throw(("As there are existing transactions against item {0}, you can not change the value of {1}").format(self.name, frappe.bold(self.meta.get_label(field))))
