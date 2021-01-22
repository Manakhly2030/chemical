from __future__ import unicode_literals
import frappe
from erpnext.stock.get_item_details import get_basic_details

@frappe.whitelist()
def get_approved_outward_sample_list(party):
    return frappe.db.get_list("Outward Sample",{"link_to":"Customer","party":party,"status":"Approved","docstatus":1},"name")


@frappe.whitelist()
def get_outward_sample_list(party):
    return frappe.db.get_list("Outward Sample",{"link_to":"Customer","party":party,"docstatus":1},"name")