from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""")
    frappe.db.sql("""update `tabWork Order` set `produced_quantity`= `produced_qty` where `docstatus` = 1""")
    work_orders= frappe.db.sql("select `name` from `tabWork Order` where `docstatus` = 1")
    for work_order in work_orders:
        qty = frappe.db.get_value("Work Order",work_order[0],"qty")
        batch_yield = frappe.db.get_value("Work Order",work_order[0],"batch_yield")

        wo_doc = frappe.get_doc("Work Order",work_orders[0])
        wo_doc.finish_item[0].bom_cost_ratio = 100
        wo_doc.finish_item[0].bom_qty_ratio = 100
        wo_doc.finish_item[0].bom_qty = qty
        wo_doc.finish_item[0].bom_yield = batch_yield
        wo_doc.flags.ignore_validate_update_after_submit = True
        wo_doc.save()
        frappe.db.commit()



            
