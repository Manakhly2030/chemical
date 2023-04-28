import frappe

def execute():
    set_valuation_method()
    set_create_new_batch()

def set_valuation_method():
    frappe.db.sql(""" Update `tabItem` SET valuation_method = null """)
    frappe.db.sql(""" Update `tabItem` Set valuation_method = "FIFO" where has_batch_no = 1 """)

def set_create_new_batch():
    frappe.db.sql(""" Update `tabItem` Set create_new_batch = 1 Where has_batch_no = 1 """)
