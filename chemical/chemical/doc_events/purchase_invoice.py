import frappe
from frappe import msgprint, _

def before_insert(self, method):
	if not self.name and self.is_opening == "Yes":
		self.naming_series = 'O' + self.naming_series
