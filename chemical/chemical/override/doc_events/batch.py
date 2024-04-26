import datetime as dt
from frappe.utils import nowdate


def before_naming(self, method):
    add_manufacturing_date_and_posting_date(self)


def add_manufacturing_date_and_posting_date(self):
    if not self.manufacturing_date:
        self.manufacturing_date = nowdate()

    if not self.posting_date and self.manufacturing_date:
        self.posting_date = dt.datetime.strptime(
            str(self.manufacturing_date), "%Y-%m-%d"
        ).strftime("%y%m%d")
