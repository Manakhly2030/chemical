import frappe

@frappe.whitelist()
def supplier_auto_name(self, method):
	if self.alias and self.supplier_name != self.alias:
		self.name = self.alias

@frappe.whitelist()
def supplier_override_after_rename(self, method, *args, **kwargs):
	Supplier.after_rename = supp_after_rename

def supp_after_rename(self, olddn, newdn, merge=False):
	if frappe.defaults.get_global_default('supp_master_name') == 'Supplier Name' and self.alias == self.supplier_name:
		frappe.db.set(self, "supplier_name", newdn)