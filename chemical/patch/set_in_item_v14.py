import frappe

def execute():
    set_valuation_method()
    set_create_new_batch()

def set_valuation_method():
    frappe.db.sql(""" Update `tabItem` SET valuation_method = null """)
    frappe.db.sql(""" Update `tabItem` Set valuation_method = "FIFO" where has_batch_no = 1 """)

def set_create_new_batch():
    frappe.db.sql(""" Update `tabItem` Set create_new_batch = 1 Where has_batch_no = 1 """)
    frappe.db.sql("""
        UPDATE `tabBatch` 
        SET use_batchwise_valuation = 1
        WHERE use_batchwise_valuation = 0
    """)

    frappe.db.set_value("Stock Settings","Stock Settings", "use_naming_series", 1)
    frappe.db.get_value("Stock Settings","Stock Settings", "naming_series_prefix", "BTH-{{ posting_date }}-.###")
    frappe.db.set_value("Stock Settings","Stock Settings", "exact_cost_valuation_for_batch_wise_items", 0)