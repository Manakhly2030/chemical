import datetime as dt
from frappe.utils import nowdate
import frappe


def before_naming(self, method):
    add_manufacturing_date_and_posting_date(self)


def add_manufacturing_date_and_posting_date(self):
    if self.reference_doctype and self.reference_name:
        self.manufacturing_date = frappe.db.get_value(self.reference_doctype, self.reference_name, "posting_date")
    
    if not self.manufacturing_date:
        self.manufacturing_date = nowdate()

    if self.manufacturing_date:
        self.posting_date = dt.datetime.strptime(str(self.manufacturing_date), "%Y-%m-%d").strftime("%y%m%d")

