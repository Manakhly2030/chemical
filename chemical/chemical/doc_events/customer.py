import frappe

@frappe.whitelist()
def customer_auto_name(self, method):
	if self.alias and self.customer_name != self.alias:
		self.name = self.alias

@frappe.whitelist()
def customer_override_after_rename(self, method, *args, **kwargs):
	Customer.after_rename = cust_after_rename

def cust_after_rename(self, olddn, newdn, merge=False):
	if frappe.defaults.get_global_default('cust_master_name') == 'Customer Name' and self.alias == self.customer_name:
		frappe.db.set(self, "customer_name", newdn)