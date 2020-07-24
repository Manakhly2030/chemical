from __future__ import unicode_literals
import unittest
import frappe
import frappe.defaults
import erpnext
from frappe.utils import flt
from datetime import date,timedelta,datetime
from frappe.model.delete_doc import check_if_doc_is_linked
import math

#def purchase_order_data_fetch:
    #d = frappe.db.sql("select * from `tabPurchase Order` where name='PO-2021-00009'",as_dict=True)
    #with open('/home/finbyz/frappe-bench/apps/evergreen/evergreen/purchase_order.json', 'a') as fp:
    #json.dump(d,fp,indent=1,default=str)
    #fp.close()

def get_company_and_warehouse():
    company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
    warehouse =  frappe.db.get_value("Warehouse",{'company':company},"name") #it will Fetch the warehouse of the given Company
    return company, warehouse

#Create New Customer
def create_customer():
    if not frappe.db.exists("Customer","Test_Customer_1"):
        customer_create = frappe.get_doc({
            "doctype":"Customer",
            "customer_name":"Test_Customer_1",
            "customer_type":"Company",
            "territory":"All Territories",
            "customer_group":"All Customer Groups"
        })
        customer_create.save()

#Create New Supplier
def create_supplier():
    if not frappe.db.exists("Supplier","Test_Supplier_1"):
        supplier_create = frappe.get_doc({
            "doctype":"Supplier",
            "supplier_name":"Test_Supplier_1",
            "supplier_group":"All Supplier Groups",
            "supplier_type":"Company",
            "country":"India"
        })
        supplier_create.save()

#Create New Item
def create_items():
    if not frappe.db.exists("Item","TEST_ITEM_1"):
        item_create = frappe.new_doc("Item")
        item_create.item_code = "TEST_ITEM_1"
        item_create.item_group = "All Item Groups"
        item_create.is_stock_item = 1
        item_create.include_item_in_manufacturing = 1
        item_create.has_batch_no = 1
        company, warehouse = get_company_and_warehouse()
        default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Stores"},"name")
        item_create.append("item_defaults",{
                "company":company,
                "default_warehouse":default_warehouse
        })
        item_create.save()

""" def create_purchase_order():
    po = frappe.new_doc("Purchase Order")
    po.naming_series = "Test-PO-.###"
    po.transaction_date = date.today()
    po.schedule_date = date.today() + timedelta(5)
    po.supplier = "Test_Supplier_1"
    po.company, po.set_warehouse = get_company_and_warehouse()
    _, warehouse = get_company_and_warehouse()
    po.append('items',{
        "item_code":"TEST_ITEM_1",
        "item_name":"TEST_ITEM_1",
        "schedule_date":date.today() + timedelta(3),
        "description":"Test_Item_for Testing",
        "qty":375.000,
        "packing_size":25,
        "packaging_material":"BAG",
        "warehouse": warehouse,
        "rate":100.00
    })
    
    po.save()
    po.submit() """


# pr = Purchase Receipt
# si = Sales Invoice
# sl = Stock Ledger Entry
# first_stock_ledger_pr_name = Stock Ledger Entry for Purchase Receipt
# first_stock_ledger_si_name = Stock Ledger Entry for Sales Invoice

first_pr_batch_no = None
second_pr_batch_no = None
third_pr_batch_no = None
first_pr_name = None
second_pr_name = None
third_pr_name = None
first_stock_ledger_pr_name = None
second_stock_ledger_pr_name = None
third_stock_ledger_pr_name = None

# Create 3 different Purchase Receipt with different date 
# pr = Purchase Receipt
def create_purchase_receipt():
    global first_pr_batch_no
    global second_pr_batch_no
    global third_pr_batch_no
    global first_pr_name
    global second_pr_name
    global third_pr_name
    global first_stock_ledger_pr_name
    global second_stock_ledger_pr_name
    global third_stock_ledger_pr_name
    company, warehouse = get_company_and_warehouse()
    cost_center = frappe.db.get_value("Company",company,"cost_center")

    #First Purchase Receipt
    first_pr = frappe.new_doc("Purchase Receipt")
    first_pr.supplier = "Test_Supplier_1"
    first_pr.naming_series = "TEST-PR-.###"
    first_pr.set_posting_time = 1
    first_pr.posting_date  = frappe.utils.add_days(frappe.utils.nowdate(), -5)
    first_pr.company, first_pr.set_warehouse = get_company_and_warehouse()
    first_pr.rejected_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")
    packaging_material = frappe.db.get_value("Packaging Material",{},"name")

    first_pr.append("items",{
        "item_code":"TEST_ITEM_1",
        "item_name":"TEST_ITEM_1",
        "description":"Test_item_1 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/1",
        "no_of_packages":5,
        "concentration":85, # type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":100.00,
        "received_qty": math.ceil(flt(25*5*(0.85*100/100))),
        "qty": math.ceil(flt(25*5*(0.85*100/100)))
    })
    first_pr.save()
    first_pr_name = first_pr.name
    first_pr.submit()
    first_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : first_pr_name}, "batch_no")
    first_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":first_pr_name},"name")

    #Second Purchase Receipt
    second_pr = frappe.new_doc("Purchase Receipt")
    second_pr.supplier = "Test_Supplier_1"
    second_pr.naming_series = "TEST-PR-.###"
    second_pr.set_posting_time = 1
    second_pr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -3)
    second_pr.company, second_pr.set_warehouse = get_company_and_warehouse()
    second_pr.rejected_warehouse =frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")

    second_pr.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "description":"Test_item_1 Details",
            "packing_size":25,
            "packaging_material": packaging_material,
            "lot_no":"Test/1",
            "no_of_packages":5,
            "concentration": 90, # type = percent
            "warehouse":warehouse,
            "cost_center":cost_center,
            "rate":125.00,
            "received_qty": math.ceil(flt(25*5*(0.90*100/100))),
            "qty": math.ceil(flt(25*5*(0.90*100/100)))
    })
    second_pr.save()
    second_pr_name = second_pr.name
    second_pr.submit()
    second_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : second_pr_name}, "batch_no")
    second_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_pr_name},"name")

    #Third Purchase Receipt
    third_pr = frappe.new_doc("Purchase Receipt")
    third_pr.supplier = "Test_Supplier_1"
    third_pr.naming_series = "TEST-PR-.###"
    third_pr.set_posting_time = 1
    third_pr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)
    third_pr.company, third_pr.set_warehouse = get_company_and_warehouse()
    third_pr.rejected_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")

    third_pr.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "description":"Test_item_1 Details",
            "packing_size":25,
            "packaging_material": packaging_material,
            "lot_no":"Test/1",
            "no_of_packages":6,
            "concentration": 88, #type = percent
            "warehouse":warehouse,
            "cost_center":cost_center,
            "rate":150.00,
            "received_qty": math.ceil(flt(25*6*(0.88*100/100))),
            "qty": math.ceil(flt(25*6*(0.88*100/100)))
    })
    third_pr.save()
    third_pr_name = third_pr.name
    third_pr.submit()
    third_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : third_pr_name}, "batch_no")
    third_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":third_pr_name},"name")


""" def create_purchase_invoice():
    first_pi = frappe.new_doc("Purchase Invoice")
    first_pi.naming_series = "Test-PURINV-.###"
    first_pi.supplier = "Test_Supplier_1"
    first_pi.set_posting_time = 1
    first_pi.posting_date = date.today()
    #first_pi.update_stock = 1
    first_pi.company, first_pi.set_warehouse = get_company_and_warehouse()
    first_pi.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "qty":100.000,
            "rate":100.00
    })
    first_pi.save()
    first_pi.submit()

    second_pi = frappe.new_doc("Purchase Invoice")
    second_pi.naming_series = "Test-PURINV-.###"
    second_pi.supplier = "Test_Supplier_1"
    second_pi.set_posting_time = 1
    second_pi.posting_date = date.today() - timedelta(3)
    second_pi.company, second_pi.set_warehouse = get_company_and_warehouse()
    #second_pi.update_stock = 1
    second_pi.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "qty":125.000,
            "rate":125.00
    })
    second_pi.save()
    second_pi.submit()

    third_pi = frappe.new_doc("Purchase Invoice")
    third_pi.naming_series = "Test-PURINV-.###"
    third_pi.supplier = "Test_Supplier_1"
    third_pi.set_posting_time = 1
    third_pi.posting_date = date.today() - timedelta(5)
    third_pi.company, third_pi.set_warehouse = get_company_and_warehouse()
    #third_pi.update_stock = 1
    third_pi.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "qty":150.000,
            "rate":150.00
    })
    third_pi.save()
    third_pi.submit() """

first_si_name = None
second_si_name = None
third_si_name = None
first_stock_ledger_si_name = None
second_stock_ledger_si_name = None
third_stock_ledger_si_name = None
    
# Create 3 different Sales Invoice 
# si = sales invoice
def create_sales_invoice():
    global first_si_name
    global second_si_name
    global third_si_name
    global first_stock_ledger_si_name
    global second_stock_ledger_si_name
    global third_stock_ledger_si_name
    company, warehouse = get_company_and_warehouse()
    cost_center = frappe.db.get_value("Company",company,"cost_center")

    #Second Sales Invoice
    second_si = frappe.new_doc("Sales Invoice")
    second_si.naming_series = "Test-SALINV-.###"
    second_si.customer = "Test_Customer_1"
    second_si.set_posting_time = 1
    second_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -2)
    second_si.company, second_si.set_warehouse = get_company_and_warehouse()
    second_si.update_stock = 1
    second_si.due_date = date.today() + timedelta(10)
    second_si.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "description":"Test_Item_1 details",
            "qty":50.000,
            "rate":225.00,
            "concentration": 90,
            "warehouse": warehouse,
            "cost_center":cost_center,
            "batch_no":second_pr_batch_no
    })

    second_si.save()
    second_si_name = second_si.name
    second_si.submit()
    second_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_si_name},"name")

    #First Sales Invoice
    first_si = frappe.new_doc("Sales Invoice")
    first_si.naming_series = "Test-SALINV-.###"
    first_si.customer = "Test_Customer_1"
    first_si.set_posting_time = 1
    first_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)
    first_si.company, first_si.set_warehouse = get_company_and_warehouse()
    first_si.update_stock = 1
    first_si.due_date = date.today() + timedelta(10)
    first_si.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "description":"Test_Item_1 details",
            "qty":50.000,
            "rate":200.00,
            "concentration": 85,
            "warehouse": warehouse,
            "cost_center": cost_center,
            "batch_no": first_pr_batch_no
    })

    first_si.save()
    first_si_name = first_si.name
    first_si.submit()
    first_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":first_si_name},"name")

    #Third Sales Invoice
    third_si = frappe.new_doc("Sales Invoice")
    third_si.naming_series = "Test-SALINV-.###"
    third_si.customer = "Test_Customer_1"
    third_si.set_posting_time = 1
    third_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(),0)
    third_si.company, third_si.set_warehouse = get_company_and_warehouse()
    third_si.update_stock = 1
    third_si.due_date = date.today() + timedelta(10)
    third_si.append("items",{
            "item_code":"TEST_ITEM_1",
            "item_name":"TEST_ITEM_1",
            "description":"Test_Item_1 details",
            "qty":50.000,
            "rate":250.00,
            "concentration": 88,
            "warehouse": warehouse,
            "cost_center":cost_center,
            "batch_no": third_pr_batch_no
    })

    third_si.save()
    third_si_name = third_si.name
    third_si.submit()
    third_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":third_si_name},"name")

class TestValuations(unittest.TestCase):
    def setUp(self):
        create_customer()
        create_supplier()
        create_items()
        #create_purchase_order()
        create_purchase_receipt()
        #create_purchase_invoice()
        create_sales_invoice()
    
    def testing(self):
        # Purchase Receipt Item

        first_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":first_pr_name},"rate")
        second_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":second_pr_name},"rate")
        third_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":third_pr_name},"rate")

        first_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":first_pr_name},"qty")
        second_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":second_pr_name},"qty")
        third_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":third_pr_name},"qty")

        # Sales Invoice Item

        first_si_rate = round((frappe.db.get_value("Sales Invoice Item",{"parent":first_si_name},"rate")),2)
        second_si_rate = round((frappe.db.get_value("Sales Invoice Item",{"parent":second_si_name},"rate")),2)
        third_si_rate = round((frappe.db.get_value("Sales Invoice Item",{"parent":third_si_name},"rate")),2)

        first_si_qty = frappe.db.get_value("Sales Invoice Item",{"parent":first_si_name},"qty")
        second_si_qty = frappe.db.get_value("Sales Invoice Item",{"parent":second_si_name},"qty")
        third_si_qty = frappe.db.get_value("Sales Invoice Item",{"parent":third_si_name},"qty")

        # Stock Ledger Entry
        # sl_pr = Stock Ledger Entry and Purchase Receipt
        # sl_si = Stock Ledger Entry and Sales Invoice

        first_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"incoming_rate")
        second_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"incoming_rate")
        third_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"incoming_rate")

        first_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"actual_qty")
        second_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"actual_qty")
        third_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"actual_qty")

        first_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"batch_no")
        second_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"batch_no")
        third_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"batch_no")

        first_sl_si_qty = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_si_name,"actual_qty")
        second_sl_si_qty = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_si_name,"actual_qty")
        third_sl_si_qty = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_si_name,"actual_qty")

        if first_sl_si_qty != 0:
            first_sl_si_incoming_rate = round(( frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_si_name,"stock_value_difference") / first_sl_si_qty),2)
        else:
            first_sl_si_incoming_rate = 0

        if second_sl_si_qty != 0:
            second_sl_si_incoming_rate = round((frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_si_name,"stock_value_difference") / second_sl_si_qty),2)
        else:
            second_sl_si_qty = 0

        if third_sl_si_qty != 0:
            third_sl_si_incoming_rate = round((frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_si_name,"stock_value_difference") / third_sl_si_qty),2)
        else:
            third_sl_si_qty = 0

        # Purchase Receipt and Stock Ledger Entry 
        self.assertEqual(first_pr_rate,first_sl_pr_incoming_rate,msg="PR1: Incoming Rate Doesn't Match")
        self.assertEqual(first_pr_qty,first_sl_pr_qty,msg="PR1: Quantity Doesn't Match")
        self.assertEqual(first_pr_batch_no,first_sl_pr_batch_no,msg="PR1: Batch ID Doesn't Match")

        self.assertEqual(second_pr_rate,second_sl_pr_incoming_rate,msg="PR2: Incoming Rate Doesn't Match")
        self.assertEqual(second_pr_qty,second_sl_pr_qty,msg="PR2: Quantity Doesn't Match")
        self.assertEqual(second_pr_batch_no,second_sl_pr_batch_no,msg="PR2: Batch ID Doesn't Match")

        self.assertEqual(third_pr_rate,third_sl_pr_incoming_rate,msg="PR3: Incoming Rate Doesn't Match")
        self.assertEqual(third_pr_qty,third_sl_pr_qty,msg="PR3: Quantity Doesn't Match")
        self.assertEqual(third_pr_batch_no,third_sl_pr_batch_no,msg="PR3: Batch ID Doesn't Match")

        # Sales Invoice and Stock Ledger Entry

        self.assertEqual(first_pr_rate,first_sl_si_incoming_rate,msg="SI1: Incoming Rate Doesn't Match")
        self.assertEqual(first_si_qty,abs(first_sl_si_qty),msg="SI1: Quantity Doesn't Match")

        self.assertEqual(second_pr_rate,second_sl_si_incoming_rate,msg="SI2: Incoming Rate Doesn't Match")
        self.assertEqual(second_si_qty,abs(second_sl_si_qty),msg="SI2: Quantity Doesn't Match")

        self.assertEqual(third_pr_rate,third_sl_si_incoming_rate,msg="SI3: Incoming Rate Doesn't Match")
        self.assertEqual(third_si_qty,abs(third_sl_si_qty),msg="SI3: Quantity Doesn't Match")

        third_si = frappe.get_doc("Sales Invoice",third_si_name)
        first_si = frappe.get_doc("Sales Invoice",first_si_name)
        second_si = frappe.get_doc("Sales Invoice",second_si_name)

        third_si.cancel()
        third_si.delete()

        first_si.cancel()
        first_si.delete()

        second_si.cancel()
        second_si.delete()
    
        third_pr = frappe.get_doc("Purchase Receipt",third_pr_name)
        second_pr = frappe.get_doc("Purchase Receipt",second_pr_name)
        first_pr = frappe.get_doc("Purchase Receipt",first_pr_name)

        third_pr.cancel()
        third_pr.delete()

        second_pr.cancel()
        second_pr.delete()

        first_pr.cancel()
        first_pr.delete()

        """ item_delete = frappe.get_doc("Item","TEST_ITEM_1")
        if check_if_doc_is_linked(item_delete):
            frappe.msgprint("item doc is linked with purchase receipt or sales invoice")
        else:
            item_delete.delete()

        supplier_delete = frappe.get_doc("Supplier","Test_Supplier_1")
        if check_if_doc_is_linked(supplier_delete):
            frappe.msgprint("supplier doc is linked with purchase receipt or sales invoice")
        else:
            supplier_delete.delete()

        customer_delete = frappe.get_doc("Customer","Test_Customer_1")
        if check_if_doc_is_linked(customer_delete):
            frappe.msgprint("customer doc is linked with purchase receipt or sales invoice")
        else:
            customer_delete.delete() """ 

del first_pr_batch_no
del second_pr_batch_no
del third_pr_batch_no
del first_pr_name
del second_pr_name
del third_pr_name
del first_stock_ledger_pr_name
del second_stock_ledger_pr_name
del third_stock_ledger_pr_name
del first_si_name
del second_si_name
del third_si_name
del first_stock_ledger_si_name
del second_stock_ledger_si_name
del third_stock_ledger_si_name







