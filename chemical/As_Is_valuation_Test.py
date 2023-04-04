from __future__ import unicode_literals
import unittest
import frappe
import frappe.defaults
import erpnext
from frappe.utils import flt
from datetime import date,timedelta,datetime
import datetime
from frappe.model.delete_doc import check_if_doc_is_linked
import math
from chemical.chemical.doc_events.work_order import make_stock_entry

# def get_company_and_warehouse():
#     company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
#     warehouse =  frappe.db.get_value("Warehouse",{'company':company},"name") #it will Fetch the warehouse of the given Company
#     return company, warehouse

#Create New Customer
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
company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company
    
if not frappe.db.exists("Item","TEST_ITEM_1"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "TEST_ITEM_1"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.gst_hsn_code = "90303990"
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.stock_uom = "Kg"
    company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
    warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    default_expense_account = frappe.db.get_value("Account",{"company":company,"account_name":"Sales Expenses"})
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","TEST_ITEM_2"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "TEST_ITEM_2"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "90319000"
    item_create.stock_uom = "Kg"
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","TEST_ITEM_3"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "TEST_ITEM_3"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "92092000"
    item_create.stock_uom = "Kg"
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","TEST_ITEM_4"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "TEST_ITEM_4"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.maintain_as_is_stock= 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "95030020"
    item_create.stock_uom = "Kg"
    company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
    warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","FINISH_TEST_ITEM"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "FINISH_TEST_ITEM"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "998942"
    item_create.stock_uom = "Kg"
    item_create.valuation_rate = 50
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","SECOND_FINISH_TEST_ITEM"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "SECOND_FINISH_TEST_ITEM"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "91149091"
    item_create.stock_uom = "Kg"
    item_create.valuation_rate = 50
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

if not frappe.db.exists("Item","AsIs_Finish_item"):
    item_create = frappe.new_doc("Item")
    item_create.item_code = "AsIs_Finish_item"
    item_create.item_group = "All Item Groups"
    item_create.is_stock_item = 1
    item_create.maintain_as_is_stock= 1
    item_create.include_item_in_manufacturing = 1
    item_create.has_batch_no = 1
    item_create.gst_hsn_code = "90308400"
    item_create.stock_uom = "Kg"
    item_create.valuation_rate = 50
    company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
    warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company
    default_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")
    item_create.append("item_defaults",{
            "company":company,
            "default_warehouse":default_warehouse,
            "expense_account":default_expense_account
    })
    item_create.save()

# if not frappe.db.exists("Manufacturer","gg"):
#     manufact = frappe.new_doc("Manufacturer")
#     manufact.short_name = "gg"
#     manufact.full_name = "gg"
#     manufact.save()
#     manufact_name = manufact.name



from frappe.utils import flt
import math

company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company

cost_center = frappe.db.get_value("Company",company,"cost_center")

#First Purchase Receipt
first_pr = frappe.new_doc("Purchase Receipt")
first_pr.supplier = "Test_Supplier_1"
first_pr.naming_series = "TEST-PR-.###"
first_pr.set_posting_time = 1
first_pr.posting_date  = frappe.utils.add_days(frappe.utils.nowdate(), -10)
first_pr.company = company
first_pr.set_warehouse = warehouse
first_pr.rejected_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")
packaging_material = frappe.db.get_value("Packaging Material",{},"name")

first_pr.append("items",{
    "item_code":"TEST_ITEM_1",
    "item_name":"TEST_ITEM_1",
    "description":"Test_item_1 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/1",
    "no_of_packages":20,
    "concentration":85, # type = percent
    "warehouse": warehouse,
    "cost_center":cost_center,
    "price":500.00,
    "rate":500.00,
    "received_qty": math.ceil(flt(25*20)),
    "qty": math.ceil(flt(25*20)),
    "quantity": math.ceil(flt(25*20*(0.85*100/100))),
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
first_pr.append("items",{
    "item_code":"TEST_ITEM_2",
    "item_name":"TEST_ITEM_2",
    "description":"Test_item_2 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/2",
    "no_of_packages":24,
    "concentration":95, # type = percent
    "warehouse":warehouse,
    "cost_center":cost_center,
    "price":250.00,
    "rate":250.00,
    "received_qty": math.ceil(flt(25*24)),
    "qty": math.ceil(flt(25*24)),
    "quantity": math.ceil(flt(25*24*(0.95*100/100))),
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
first_pr.append("items",{
    "item_code":"TEST_ITEM_3",
    "item_name":"TEST_ITEM_3",
    "description":"Test_item_3 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/3",
    "no_of_packages":28,
    "concentration":90, # type = percent
    "warehouse":warehouse,
    "cost_center":cost_center,
    "price":80,
    "rate":80,
    "received_qty": math.ceil(flt(25*28)),
    "qty": math.ceil(flt(25*28)),
    "quantity": math.ceil(flt(25*28*(0.90*100/100))),
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
first_pr.append("items",{
    "item_code":"TEST_ITEM_4",
    "item_name":"TEST_ITEM_4",
    "description":"Test_item_4 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/4",
    "no_of_packages":30,
    "concentration":90, # type = percent
    "supplier_concentration":90,
    "warehouse": warehouse,
    "cost_center":cost_center,
    "price":40,
    "quantity": math.ceil(flt(25*30*(0.90*100/100))),
    "qty": math.ceil(flt(((25*30*(0.90*100/100))*100)/90)),  #qty=quantity*100/concentration
    "received_qty": math.ceil(flt(((25*30*(0.90*100/100))*100)/90)),      #qty = received_qty
    "rate": math.ceil(flt(((25*30*(0.90*100/100))*40)/(((25*30*(0.90*100/100))*100)/90))) #rate=quantity*price/qty
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
first_pr.save()
first_pr_name = first_pr.name
first_pr.submit()
first_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : first_pr_name,"item_code":"TEST_ITEM_1"}, "batch_no")
first_pr_concentration = frappe.db.get_value("Purchase Receipt Item",{"parent" : first_pr_name,"item_code":"TEST_ITEM_1"}, "concentration")
first_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":first_pr_name,"item_code":"TEST_ITEM_1"},"name")

#Second Purchase Receipt
second_pr = frappe.new_doc("Purchase Receipt")
second_pr.supplier = "Test_Supplier_1"
second_pr.naming_series = "TEST-PR-.###"
second_pr.set_posting_time = 1
second_pr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -8)
second_pr.company = company
second_pr.set_warehouse = warehouse
second_pr.rejected_warehouse =frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")

second_pr.append("items",{
        "item_code":"TEST_ITEM_1",
        "item_name":"TEST_ITEM_1",
        "description":"Test_item_1 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/1",
        "no_of_packages":28,
        "concentration": 95, # type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":530,
        "price": 530,
        "received_qty": math.ceil(flt(25*28)),
        "qty": math.ceil(flt(25*28)),
        "quantity": math.ceil(flt(25*28*(0.95*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
second_pr.append("items",{
        "item_code":"TEST_ITEM_2",
        "item_name":"TEST_ITEM_2",
        "description":"Test_item_2 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/2",
        "no_of_packages":30,
        "concentration": 90, # type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":240,
        "price": 240,
        "received_qty": math.ceil(flt(25*30)),
        "qty": math.ceil(flt(25*30)),
        "quantity": math.ceil(flt(25*30*(0.90*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
second_pr.append("items",{
        "item_code":"TEST_ITEM_3",
        "item_name":"TEST_ITEM_3",
        "description":"Test_item_3 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/3",
        "no_of_packages":32,
        "concentration": 85, # type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":78,
        "price": 78,
        "received_qty": math.ceil(flt(25*32)),
        "qty": math.ceil(flt(25*32)),
        "quantity": math.ceil(flt(25*32*(0.85*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
second_pr.append("items",{
    "item_code":"TEST_ITEM_4",
    "item_name":"TEST_ITEM_4",
    "description":"Test_item_4 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/4",
    "no_of_packages":20,
    "concentration":90, # type = percent
    "supplier_concentration":90,
    "warehouse": warehouse,
    "cost_center":cost_center,
    "price":48,
    "quantity": math.ceil(flt(25*20*(0.90*100/100))),
    "qty": math.ceil(flt(((25*20*(0.90*100/100))*100)/90)),  #qty=quantity*100/concentration
    "received_qty":  math.ceil(flt((25*20*(0.90*100/100)*100)/90)),  #qty = received_qty
    "rate": math.ceil(flt(((25*20*(0.90*100/100))*48)/(((25*20*(0.90*100/100))*100)/90)))   #rate=quantity*price/qty 
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
second_pr.save()
second_pr_name = second_pr.name
second_pr.submit()
second_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : second_pr_name,"item_code":"TEST_ITEM_2"}, "batch_no")
second_pr_concentration = frappe.db.get_value("Purchase Receipt Item",{"parent" : second_pr_name,"item_code":"TEST_ITEM_2"}, "concentration")
second_pr_third_item_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : second_pr_name,"item_code":"TEST_ITEM_3"}, "batch_no")
second_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_pr_name,"item_code":"TEST_ITEM_2"},"name")

#Third Purchase Receipt
third_pr = frappe.new_doc("Purchase Receipt")
third_pr.supplier = "Test_Supplier_1"
third_pr.naming_series = "TEST-PR-.###"
third_pr.set_posting_time = 1
third_pr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -5)
third_pr.company = company
third_pr.set_warehouse = warehouse

third_pr.rejected_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")

third_pr.append("items",{
        "item_code":"TEST_ITEM_1",
        "item_name":"TEST_ITEM_1",
        "description":"Test_item_1 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/1",
        "no_of_packages":36,
        "concentration": 95, #type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "price": 510.00,
        "rate":510.00,
        "received_qty": math.ceil(flt(25*36)),
        "qty": math.ceil(flt(25*36)),
        "quantity": math.ceil(flt(25*36*(0.95*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
third_pr.append("items",{
        "item_code":"TEST_ITEM_2",
        "item_name":"TEST_ITEM_2",
        "description":"Test_item_2 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/2",
        "no_of_packages":40,
        "concentration": 85, #type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":275,
        "price": 275,
        "received_qty": math.ceil(flt(25*40)),
        "qty": math.ceil(flt(25*40)),
        "quantity": math.ceil(flt(25*40*(0.85*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
third_pr.append("items",{
        "item_code":"TEST_ITEM_3",
        "item_name":"TEST_ITEM_3",
        "description":"Test_item_3 Details",
        "packing_size":25,
        "packaging_material": packaging_material,
        "lot_no":"Test/3",
        "no_of_packages":44,
        "concentration": 95, #type = percent
        "warehouse":warehouse,
        "cost_center":cost_center,
        "rate":88,
        "price": 88,
        "received_qty": math.ceil(flt(25*44)),
        "qty": math.ceil(flt(25*44)),
        "quantity": math.ceil(flt(25*44*(0.95*100/100))),
        #"manufacturer":"gg",
        #"manufacturer_part_no":"gg"
})
third_pr.append("items",{
    "item_code":"TEST_ITEM_4",
    "item_name":"TEST_ITEM_4",
    "description":"Test_item_4 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/4",
    "no_of_packages":60,
    "concentration":90, # type = percent,
    "supplier_concentration":90,
    "warehouse": warehouse,
    "cost_center":cost_center,
    "price":50,
    "quantity": math.ceil(flt(25*60*(0.90*100/100))),
    "qty": math.ceil(flt((25*60*(0.90*100/100)*100)/90)),  #qty=quantity*100/concentration
    "received_qty": math.ceil(flt((25*60*(0.90*100/100)*100)/90)),
    "rate": math.ceil(flt(((25*60*(0.90*100/100))*50)/((25*60*(0.90*100/100)*100)/90)))
   
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
third_pr.save()
third_pr_name = third_pr.name
third_pr.submit()
third_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : third_pr_name,"item_code":"TEST_ITEM_3"}, "batch_no")
third_pr_concentration = frappe.db.get_value("Purchase Receipt Item",{"parent" : third_pr_name,"item_code":"TEST_ITEM_3"}, "concentration")
third_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":third_pr_name,"item_code":"TEST_ITEM_3"},"name")

#fourth purchase receipt for test_item_4
fourth_pr = frappe.new_doc("Purchase Receipt")
fourth_pr.supplier = "Test_Supplier_1"
fourth_pr.naming_series = "TEST-PR-.###"
fourth_pr.set_posting_time = 1
fourth_pr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -5)
fourth_pr.company = company
fourth_pr.set_warehouse = warehouse
fourth_pr.rejected_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")

fourth_pr.append("items",{
    "item_code":"TEST_ITEM_4",
    "item_name":"TEST_ITEM_4",
    "description":"Test_item_4 Details",
    "packing_size":25,
    "packaging_material": packaging_material,
    "lot_no":"Test/4",
    "no_of_packages":60,
    "concentration":90, # type = percent,
    "supplier_concentration":90,
    "warehouse": warehouse,
    "cost_center":cost_center,
    "price":55,
    "quantity": math.ceil(flt(25*60*(0.90*100/100))),
    "qty": math.ceil(flt((25*60*(0.90*100/100)*100)/90)),  #qty=quantity*100/concentration
    "received_qty": math.ceil(flt((25*60*(0.90*100/100)*100)/90)), #qty = received_qty
    "rate":math.ceil(flt(((25*60*(0.90*100/100))*55)/((25*60*(0.90*100/100)*100)/90))),  #rate=quantity*price/qty
   
    #"manufacturer":"gg",
    #"manufacturer_part_no":"gg"
})
fourth_pr.save()
fourth_pr_name = fourth_pr.name
fourth_pr.submit()
fourth_pr_batch_no = frappe.db.get_value("Purchase Receipt Item",{"parent" : fourth_pr_name,"item_code":"TEST_ITEM_4"}, "batch_no")
fourth_pr_concentration = frappe.db.get_value("Purchase Receipt Item",{"parent" : fourth_pr_name,"item_code":"TEST_ITEM_4"}, "concentration")
fourth_stock_ledger_pr_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":fourth_pr_name,"item_code":"TEST_ITEM_4"},"name")

# from datetime import date,timedelta,datetime
# import datetime
# second_si_name = None
# second_stock_ledger_si_name = None
# company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
# warehouse =  frappe.db.get_value("Warehouse",{'company':company},"name") #it will Fetch the warehouse of the given Company
# cost_center = frappe.db.get_value("Company",company,"cost_center")
# second_si = frappe.new_doc("Sales Invoice")
# second_si.naming_series = "Test-SALINV-.###"
# second_si.customer = "Test_Customer_1"
# second_si.set_posting_time = 1
# second_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -4)
# second_si.company = company
# second_si.set_warehouse = warehouse
# second_si.update_stock = 1
# second_si.due_date = date.today() + timedelta(10)

# second_si.append("items",{
#         "item_code":"TEST_ITEM_1",
#         "item_name":"TEST_ITEM_1",
#         "description":"Test_Item_1 details",
#         "qty":50.000,
#         "quantity": 50,
#         "rate":600.00,
#         "price": 600,
#         "concentration": 85,
#         "warehouse": warehouse,
#         "cost_center":cost_center,
#         "batch_no":first_pr_batch_no,
#         "manufacturer":"gg",
#         "manufacturer_part_no":"gg"
# })
# second_si.append("items",{
#         "item_code":"TEST_ITEM_2",
#         "item_name":"TEST_ITEM_2",
#         "description":"Test_Item_2 details",
#         "qty":50.000,
#         "quantity": 50,
#         "rate":350.00,
#         "price": 350,
#         "concentration": 90,
#         "warehouse": warehouse,
#         "cost_center":cost_center,
#         "batch_no":second_pr_batch_no,
#         "manufacturer":"gg",
#         "manufacturer_part_no":"gg"
# })
# second_si.append("items",{
#         "item_code":"TEST_ITEM_3",
#         "item_name":"TEST_ITEM_3",
#         "description":"Test_Item_3 details",
#         "qty":50.000,
#         "quantity": 50,
#         "price": 250,
#         "rate":250.00,
#         "concentration": 95,
#         "warehouse": warehouse,
#         "cost_center":cost_center,
#         "batch_no":third_pr_batch_no,
#         "manufacturer":"gg",
#         "manufacturer_part_no":"gg"
# })
# second_si.append("items",{
#         "item_code":"TEST_ITEM_4",
#         "item_name":"TEST_ITEM_4",
#         "description":"Test_Item_4 details",
#         "quantity":50,
#         "price": 150,
#         "qty": (flt((50*100)/97)),                                    #qty=quantity*100/concentration   
#         "rate": math.ceil(flt((50*150)/((50*100)/97))),               #rate= quantity*price/qty
#         "concentration": 97,
#         "warehouse": warehouse,
#         "cost_center":cost_center,
#         "batch_no":fourth_pr_batch_no,
#         "manufacturer":"gg",
#         "manufacturer_part_no":"gg"
# })

# second_si.save()
# second_si_name = second_si.name
# second_si.submit()
# second_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_si_name},"name")

# first_si_name = None
# second_si_name = None
# third_si_name = None
# first_stock_ledger_si_name = None
# second_stock_ledger_si_name = None
# third_stock_ledger_si_name = None

# def create_sales_invoice():
#     from datetime import date,timedelta,datetime
#     import datetime
#     # global first_si_name
#     global second_si_name
#     # global third_si_name
#     # global first_stock_ledger_si_name
#     global second_stock_ledger_si_name
#     # global third_stock_ledger_si_name
#     company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
#     warehouse =  frappe.db.get_value("Warehouse",{'company':company},"name") #it will Fetch the warehouse of the given Company
#     cost_center = frappe.db.get_value("Company",company,"cost_center")

#     #Second Sales Invoice
#     second_si = frappe.new_doc("Sales Invoice")
#     second_si.naming_series = "Test-SALINV-.###"
#     second_si.customer = "Test_Customer_1"
#     second_si.set_posting_time = 1
#     second_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -4)
#     second_si.company = company
#     second_si.set_warehouse = warehouse
#     second_si.update_stock = 1
#     second_si.due_date = date.today() + timedelta(10)
#     second_si.append("items",{
#             "item_code":"TEST_ITEM_1",
#             "item_name":"TEST_ITEM_1",
#             "description":"Test_Item_1 details",
#             "qty":50.000,
#             "quantity": 50,
#             "rate":600.00,
#             "price": 600,
#             "concentration": 85,
#             "warehouse": warehouse,
#             "cost_center":cost_center,
#             "batch_no":first_pr_batch_no,
#             "manufacturer":"gg",
#             "manufacturer_part_no":"gg"
#     })
#     second_si.append("items",{
#             "item_code":"TEST_ITEM_2",
#             "item_name":"TEST_ITEM_2",
#             "description":"Test_Item_2 details",
#             "qty":50.000,
#             "quantity": 50,
#             "rate":350.00,
#             "price": 350,
#             "concentration": 90,
#             "warehouse": warehouse,
#             "cost_center":cost_center,
#             "batch_no":second_pr_batch_no,
#             "manufacturer":"gg",
#             "manufacturer_part_no":"gg"
#     })
#     second_si.append("items",{
#             "item_code":"TEST_ITEM_3",
#             "item_name":"TEST_ITEM_3",
#             "description":"Test_Item_3 details",
#             "qty":50.000,
#             "quantity": 50,
#             "price": 250,
#             "rate":250.00,
#             "concentration": 95,
#             "warehouse": warehouse,
#             "cost_center":cost_center,
#             "batch_no":third_pr_batch_no,
#             "manufacturer":"gg",
#             "manufacturer_part_no":"gg"
#     })
#     second_si.append("items",{
#             "item_code":"TEST_ITEM_4",
#             "item_name":"TEST_ITEM_4",
#             "description":"Test_Item_4 details",
#             "quantity":50,
#             "price": 150,
#             "qty": (flt((50*100)/97)),                                    #qty=quantity*100/concentration   
#             "rate": math.ceil(flt((50*150)/((50*100)/97))),               #rate= quantity*price/qty
#             "concentration": 97,
#             "warehouse": warehouse,
#             "cost_center":cost_center,
#             "batch_no":second_pr_batch_no,
#             "manufacturer":"gg",
#             "manufacturer_part_no":"gg"
#     })

#     second_si.save()
#     second_si_name = second_si.name
#     second_si.submit()
#     second_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_si_name},"name")

    # First Sales Invoice
    # first_si = frappe.new_doc("Sales Invoice")
    # first_si.naming_series = "Test-SALINV-.###"
    # first_si.customer = "Test_Customer_1"
    # first_si.set_posting_time = 1
    # first_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -3)
    # first_si.company = company
    # first_si.set_warehouse = warehouse
    # first_si.update_stock = 1
    # first_si.due_date = date.today() + timedelta(10)
    # first_si.append("items",{
    #         "item_code":"TEST_ITEM_1",
    #         "item_name":"TEST_ITEM_1",
    #         "description":"Test_Item_1 details",
    #         "qty":100.000,
    #         "rate":600.00,
    #         "concentration": 85,
    #         "warehouse": warehouse,
    #         "cost_center": cost_center,
    #         "batch_no": first_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })
    # first_si.append("items",{
    #         "item_code":"TEST_ITEM_2",
    #         "item_name":"TEST_ITEM_2",
    #         "description":"Test_Item_2 details",
    #         "qty":100.000,
    #         "rate":550.00,
    #         "concentration": 95,
    #         "warehouse": warehouse,
    #         "cost_center": cost_center,
    #         "batch_no": second_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })
    # first_si.append("items",{
    #         "item_code":"TEST_ITEM_3",
    #         "item_name":"TEST_ITEM_3",
    #         "description":"Test_Item_3 details",
    #         "qty":100.000,
    #         "rate":500.00,
    #         "concentration": 90,
    #         "warehouse": warehouse,
    #         "cost_center": cost_center,
    #         "batch_no": third_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })

    # first_si.save()
    # first_si_name = first_si.name
    # first_si.submit()
    # first_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":first_si_name},"name")

    # #Third Sales Invoice
    # third_si = frappe.new_doc("Sales Invoice")
    # third_si.naming_series = "Test-SALINV-.###"
    # third_si.customer = "Test_Customer_1"
    # third_si.set_posting_time = 1
    # third_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -2)
    # third_si.company = company
    # third_si.set_warehouse = warehouse
    # third_si.update_stock = 1
    # third_si.due_date = date.today() + timedelta(10)
    # third_si.append("items",{
    #         "item_code":"TEST_ITEM_1",
    #         "item_name":"TEST_ITEM_1",
    #         "description":"Test_Item_1 details",
    #         "qty":100.000,
    #         "rate":150.00,
    #         "concentration": 95,
    #         "warehouse": warehouse,
    #         "cost_center":cost_center,
    #         "batch_no": first_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })
    # third_si.append("items",{
    #         "item_code":"TEST_ITEM_2",
    #         "item_name":"TEST_ITEM_2",
    #         "description":"Test_Item_2 details",
    #         "qty":100.000,
    #         "rate":200.00,
    #         "concentration": 85,
    #         "warehouse": warehouse,
    #         "cost_center":cost_center,
    #         "batch_no": second_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })
    # third_si.append("items",{
    #         "item_code":"TEST_ITEM_3",
    #         "item_name":"TEST_ITEM_3",
    #         "description":"Test_Item_3 details",
    #         "qty":100.000,
    #         "rate":250.00,
    #         "concentration": 90,
    #         "warehouse": warehouse,
    #         "cost_center":cost_center,
    #         "batch_no": third_pr_batch_no,
    #         "manufacturer":"gg",
    #         "manufacturer_part_no":"gg"
    # })

    # third_si.save()
    # third_si_name = third_si.name
    # third_si.submit()
    # third_stock_ledger_si_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":third_si_name},"name")



# Create BOM-1
bom_create = frappe.new_doc("BOM")
bom_create.item = "FINISH_TEST_ITEM"
company =  frappe.db.get_value("Company",{},"company_name")
bom_create.company = company
bom_create.quantity = 500.00
bom_create.based_on = "TEST_ITEM_1"
bom_create.is_multiple_item= 1
bom_create.total_quantity = 1000
bom_create.batch_yield= 10
bom_create.concentration = 100
bom_create.append("items",{
    "item_code" : "TEST_ITEM_1",
    "item_name" : "TEST_ITEM_1",
    "qty": 100,
    "rate": 515.93,
})
bom_create.append("items",{
    "item_code" : "TEST_ITEM_2",
    "item_name" : "TEST_ITEM_2",
    "qty": 100,
    "uom":"Foot",
    "rate": 256.11
})
bom_create.append("items",{
    "item_code" : "TEST_ITEM_3",
    "item_name" : "TEST_ITEM_3",
    "qty": 100,
    "uom":"Foot",
    "rate": 82.61
})
bom_create.append("items",{
    "item_code" : "TEST_ITEM_4",
    "item_name" : "TEST_ITEM_4",
    "qty": 100,
    "uom":"Foot",
    "rate": 224.81,    
})
# new functionality 
bom_create.append("multiple_finish_item",{
    "item_code": "FINISH_TEST_ITEM",
    "cost_ratio": 60,
    "qty_ratio": 50,
    "qty": 500,
    "uom":"Foot",
    "batch_yield": 5,
})
bom_create.append("multiple_finish_item",{
    "item_code": "SECOND_FINISH_TEST_ITEM",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "uom":"Foot",
    "batch_yield": 2.5,
})
bom_create.append("multiple_finish_item",{
    "item_code": "AsIs_Finish_item",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "uom":"Foot",
    "batch_yield": 2.5,
})
bom_create.append("additional_cost",{
    "description": "Labour Cost",
    "qty": 1000,
    "uom": "FG QTY",
    "rate": 200,
    "uom":"Foot",
    "amount": 200000,
})


bom_create.save()
bom_name = bom_create.name
bom_create.submit()

# Create BOM-2
bom2_create = frappe.new_doc("BOM")
bom2_create.item = "SECOND_FINISH_TEST_ITEM"
company =  frappe.db.get_value("Company",{},"company_name")
bom2_create.company = company
bom2_create.quantity = 500.00
bom2_create.based_on = "TEST_ITEM_1"
bom2_create.is_multiple_item= 1
bom2_create.total_quantity = 1000
bom2_create.batch_yield= 10
bom2_create.concentration = 100
bom2_create.append("items",{
    "item_code" : "TEST_ITEM_1",
    "item_name" : "TEST_ITEM_1",
    "qty": 100,
    "rate": 515.93,
})
bom2_create.append("items",{
    "item_code" : "TEST_ITEM_2",
    "item_name" : "TEST_ITEM_2",
    "qty": 100,
    "rate": 256.11
})
bom2_create.append("items",{
    "item_code" : "TEST_ITEM_3",
    "item_name" : "TEST_ITEM_3",
    "qty": 100,
    "rate": 82.61
})
bom2_create.append("items",{
    "item_code" : "TEST_ITEM_4",
    "item_name" : "TEST_ITEM_4",
    "qty": 100,
    "rate": 224.81,    
})
# new functionality 

bom2_create.append("multiple_finish_item",{
    "item_code": "SECOND_FINISH_TEST_ITEM",
    "cost_ratio": 60,
    "qty_ratio": 50,
    "qty": 500,
    "batch_yield": 5,
})
bom2_create.append("multiple_finish_item",{
    "item_code": "AsIs_Finish_item",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "batch_yield": 2.5,
})
bom2_create.append("multiple_finish_item",{
    "item_code": "FINISH_TEST_ITEM",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "batch_yield": 2.5,
})

bom2_create.save()
bom2_name = bom2_create.name
bom2_create.submit()

# Create BOM-3
bom3_create = frappe.new_doc("BOM")
bom3_create.item = "AsIs_Finish_item"
company =  frappe.db.get_value("Company",{},"company_name")
bom3_create.company = company
bom3_create.quantity = 500.00
bom3_create.based_on = "TEST_ITEM_1"
bom3_create.is_multiple_item= 1
bom3_create.total_quantity = 1000
bom3_create.batch_yield= 10
bom3_create.concentration = 100
bom3_create.append("items",{
    "item_code" : "TEST_ITEM_1",
    "item_name" : "TEST_ITEM_1",
    "qty": 100,
    "rate": 515.93,
})
bom3_create.append("items",{
    "item_code" : "TEST_ITEM_2",
    "item_name" : "TEST_ITEM_2",
    "qty": 100,
    "rate": 256.11
})
bom3_create.append("items",{
    "item_code" : "TEST_ITEM_3",
    "item_name" : "TEST_ITEM_3",
    "qty": 100,
    "rate": 82.61
})
bom3_create.append("items",{
    "item_code" : "TEST_ITEM_4",
    "item_name" : "TEST_ITEM_4",
    "qty": 100,
    "rate": 224.81,    
})
# new functionality 

bom3_create.append("multiple_finish_item",{
    "item_code": "AsIs_Finish_item",
    "cost_ratio": 60,
    "qty_ratio": 50,
    "qty": 500,
    "batch_yield": 5,
})
bom3_create.append("multiple_finish_item",{
    "item_code": "FINISH_TEST_ITEM",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "batch_yield": 2.5,
})
bom3_create.append("multiple_finish_item",{
    "item_code": "SECOND_FINISH_TEST_ITEM",
    "cost_ratio": 20,
    "qty_ratio": 25,
    "qty": 250,
    "batch_yield": 2.5,
})

bom3_create.save()
bom3_name = bom3_create.name
bom3_create.submit()


# Create Work Order
from datetime import date,timedelta,datetime
import datetime

work_order_create = frappe.new_doc("Work Order")
work_order_create.naming_series = "Test-WO-.###"
work_order_create.production_item = "FINISH_TEST_ITEM"
work_order_create.qty = 200
work_order_create.batch_yield = 10
work_order_create.is_multiple_item = 1
company =  frappe.db.get_value("Company",{},"company_name")
work_order_create.wip_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"Work In Progress"},"name")
work_order_create.fg_warehouse = "Finished Goods - CI"
work_order_create.bom_no = "BOM-FINISH_TEST_ITEM-001"
work_order_create.concentration = 0
work_order_create.use_multi_level_bom = 1
work_order_create.based_on = "TEST_ITEM_1"
d = datetime.datetime.now() - timedelta(days=1,hours=10)
d.strftime("%d-%m-%Y %H:%M:%S")
work_order_create.planned_start_date = d
work_order_store_warehouse = frappe.db.get_value("Warehouse",{"company":company, "warehouse_name":"RAW MATERIAL"},"name")

# work_order_create.append("finish_item",{
#     "item_code": "FINISH_TEST_ITEM",
#     "bom_cost_ratio": 60,
#     "bom_qty_ratio" : 50,
#     "bom_qty": 100,
#     "bom_yield": 5,
#     "source_warehouse" : work_order_store_warehouse
# })
# work_order_create.append("finish_item",{
#     "item_code": "SECOND_FINISH_TEST_ITEM",
#     "bom_cost_ratio": 20,
#     "bom_qty_ratio":25,
#     "bom_qty": 50,
#     "bom_yield": 2.5,
#     "source_warehouse" : work_order_store_warehouse
# })
# work_order_create.append("finish_item",{
#     "item_code": "AsIs_Finish_item",
#     "bom_cost_ratio": 20,
#     "bom_qty_ratio":25,
#     "bom_qty": 50,
#     "bom_yield": 2.5,
#     "source_warehouse" : work_order_store_warehouse
# })

work_order_create.save()
work_name = work_order_create.name
work_order_create.submit()


# mtm = Material Transfer For Manufacture
# Create Stock Entry of Material Transfer For Manufacture (mtm)
from chemical.chemical.doc_events.work_order import make_stock_entry

stock_entry_mtm = frappe.new_doc("Stock Entry")
stock_entry_mtm.update(make_stock_entry(work_name,"Material Transfer for Manufacture", qty=200))
stock_entry_mtm.naming_series = "Test-MTM-.###"
stock_entry_mtm.set_posting_time = 1
stock_entry_mtm.based_on = "TEST_ITEM_1"
stock_entry_mtm.from_bom = 1
stock_entry_mtm.use_multi_level_bom = 1
stock_entry_mtm.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)
company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") #it will Fetch the warehouse of the given Company
stock_entry_mtm.from_warehouse = warehouse
stock_entry_mtm.items[0].quantity = 80
stock_entry_mtm.items[1].quantity = 80
stock_entry_mtm.items[2].quantity = 80
stock_entry_mtm.items[3].quantity = 80
stock_entry_mtm.items[0].qty = 80
stock_entry_mtm.items[1].qty = 80
stock_entry_mtm.items[2].qty = 80
stock_entry_mtm.items[3].qty = 88.888889
# stock_entry_mtm.items[0].price = 515.95
# stock_entry_mtm.items[1].price = 256.13
# stock_entry_mtm.items[2].price = 82.6
# stock_entry_mtm.items[3].price = 225.45
stock_entry_mtm.items[0].batch_no = first_pr_batch_no
stock_entry_mtm.items[1].batch_no = second_pr_batch_no
stock_entry_mtm.items[2].batch_no = third_pr_batch_no
stock_entry_mtm.items[3].batch_no = fourth_pr_batch_no

stock_entry_mtm.items[0].concentration = first_pr_concentration
stock_entry_mtm.items[1].concentration = second_pr_concentration
stock_entry_mtm.items[2].concentration = third_pr_concentration
stock_entry_mtm.items[3].concentration = fourth_pr_concentration


stock_entry_mtm.save()
stock_entry_mtm_name = stock_entry_mtm.name
stock_entry_mtm.submit()
first_stock_ledger_mtm_item_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_mtm_name,"item_code":"TEST_ITEM_1"},"name")
second_stock_ledger_mtm_item_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_mtm_name,"item_code":"TEST_ITEM_2"},"name")
third_stock_ledger_mtm_item_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_mtm_name,"item_code":"TEST_ITEM_3"},"name")
fourth_stock_ledger_mtm_item_name = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_mtm_name,"item_code":"TEST_ITEM_4"},"name")

# # Create Stock Entry for Material Receipt 1 (mr_1)
# from datetime import date,timedelta,datetime
# import datetime
# stock_entry_mr = frappe.new_doc("Stock Entry")
# stock_entry_mr.naming_series = "Test-MR-.###"
# stock_entry_mr.stock_entry_type = "Material Receipt"
# stock_entry_mr.set_posting_time = 1
# stock_entry_mr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), -1)
# company = frappe.db.get_value("Company",{},"company_name") 
# warehouse = frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"FINISHED GOODS(CRUDE)"},"name")
# packaging_material = frappe.db.get_value("Packaging Material",{},"name")
# stock_entry_mr.to_warehouse = warehouse
# stock_entry_mr.append("items",{
#     "t_warehouse": warehouse,
#     "item_code": "FINISH_TEST_ITEM",
#     "qty": 50,
#     "quantity": 50,
#     "concentration": 90,
#     "basic_rate": 82,           #basic rate is calculated automatically as valuaton rate.
#     "price": 82,            #not needed as basic rate is calculated automatically as valuaton rate.
#     "packing_size": 25,
#     "no_of_packages":2,
#     "actual_qty": 50,
#     "actual_valuation_rate":(25*2*(90/100)),
#     "packing_material": packaging_material
# })
# stock_entry_mr.save()
# stock_entry_mr_1_name = stock_entry_mr.name
# stock_entry_mr.submit()
# stock_entry_mr_1_batch_no = frappe.db.get_value("Batch",{"reference_name": stock_entry_mr_1_name},"name")

# Create Stock Entry for Manufacture (ma)
from datetime import date,timedelta,datetime
import datetime
from chemical.chemical.doc_events.work_order import make_stock_entry

stock_entry_ma = frappe.new_doc("Stock Entry")
stock_entry_ma.update(make_stock_entry(work_name,"Manufacture", qty=200))
stock_entry_ma.stock_entry_type= "Manufacture"
stock_entry_ma.naming_series = "Test-MA-.###"
stock_entry_ma.set_posting_time = 1
stock_entry_ma.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), 0)
stock_entry_ma.based_on = "TEST_ITEM_1"
stock_entry_ma.fg_completed_quantity = 200
stock_entry_ma.fg_completed_qty = 205.556
stock_entry_ma.from_warehouse = warehouse
target_warehouse =  frappe.db.get_value("Warehouse",{'company': company, 'warehouse_name': 'FINISHED GOODS(CRUDE)'},"name") #it will Fetch the warehouse of the given Company
stock_entry_ma.to_warehouse = target_warehouse
# stock_entry_ma.items[3].concentration = 85
for item in stock_entry_ma.items:
    if item.item_code == "TEST_ITEM_1":
        item.batch_no = first_pr_batch_no
        item.concentration = first_pr_concentration
        item.quantity = 80
        item.qty = 80
    elif item.item_code == "TEST_ITEM_2":
        item.batch_no = second_pr_batch_no
        item.concentration = second_pr_concentration
        item.quantity = 80
        item.qty = 80
    elif item.item_code == "TEST_ITEM_3":
        item.batch_no = third_pr_batch_no
        item.concentration = third_pr_concentration
        item.quantity = 80
        item.qty = 80
    elif item.item_code == "TEST_ITEM_4":
        item.batch_no = fourth_pr_batch_no
        item.concentration = fourth_pr_concentration
        item.quantity = 80
        item.qty = 88.889
    elif item.item_code == "FINISH_TEST_ITEM":
        item.concentration = 100
        item.packing_size = 25
        item.no_of_packages = 0
        item.lot_no = "Test/Finish"
        item.packaging_material = packaging_material
        item.quantity = 100
        item.qty = 100
        item.is_finished_item = 1
        item.bom_no = "BOM-FINISH_TEST_ITEM-001"
    elif item.item_code == "SECOND_FINISH_TEST_ITEM":
        item.concentration = 100
        item.packing_size = 25
        item.no_of_packages = 0
        item.lot_no = "Test/SecondFinish"
        item.packaging_material = packaging_material
        item.quantity = 50
        item.qty = 50
        item.is_finished_item = 1
        item.bom_no = "BOM-SECOND_FINISH_TEST_ITEM-001"
    elif item.item_code == "AsIs_Finish_item":
        item.concentration = 90
        item.packing_size = 25
        item.no_of_packages = 0
        item.lot_no = "Test/AsIs"
        item.packaging_material = packaging_material
        item.quantity = 50
        item.qty = 55.556
        item.is_finished_item = 1
        item.bom_no = "BOM-AsIs_Finish_item-001"
# stock_entry_ma.append("items",{
#    "s_warehouse": warehouse,
#     "item_code": "TEST_ITEM_1",
#     "batch_no": first_pr_batch_no,
#     "qty": 10,
#     "quantity": 10,
#     "concentration": 90,
#     "basic_rate": 82,          
#     "price": 82,            
#     "packing_size": 25,
#     "no_of_packages":2,
#     "actual_qty": 50,
#     "actual_valuation_rate":(25*2*(90/100)),
#     "packing_material": packaging_material
# })

# stock_entry_ma.append("items",{
#    "s_warehouse": warehouse,
#     "item_code": "TEST_ITEM_2",
#     "batch_no": second_pr_batch_no,
#     "qty":10,
#     "quantity":10,
#     "concentration": 80,
#     "basic_rate": 85,          
#     "price": 85,            
#     "packing_size": 25,
#     "no_of_packages":3,
#     "actual_qty": 40,
#     "actual_valuation_rate":(25*3*(80/100)),
#     "packing_material": packaging_material
# })

# stock_entry_ma.append("items",{
#     "s_warehouse": warehouse,
#     "item_code": "TEST_ITEM_3",
#     "batch_no": third_pr_batch_no,
#     "qty": 10,
#     "quantity": 10,
#     "concentration": 90,
#     "basic_rate": 82,          
#     "price": 82,            
#     "packing_size": 20,
#     "no_of_packages":2,
#     "actual_qty": 50,
#     "actual_valuation_rate":(20*2*(90/100)),
#     "packing_material": packaging_material
# })

# stock_entry_ma.append("items",{
#     "s_warehouse": warehouse,
#     "item_code": "TEST_ITEM_4",
#     "batch_no": fourth_pr_batch_no,
#     "qty": 10,
#     "quantity": 10,
#     "concentration": 98,
#     "basic_rate": 82,          
#     "price": 82,            
#     "packing_size": 25,
#     "no_of_packages":2,
#     "actual_qty": 50,
#     "actual_valuation_rate":(25*2*(98/100)),
#     "packing_material": packaging_material
# })

# stock_entry_ma.append("items",{
#     "item_code": frappe.db.get_value("Work Order",work_name,"production_item"),
#     "t_warehouse": target_warehouse,
#     "qty": 10,
#     "quantity": 10,
#     "concentration": 98,
#     "price":90,
#     "basic_rate":90
# })

stock_entry_ma.save()
stock_entry_ma_name = stock_entry_ma.name
stock_entry_ma.submit()
final_item_batch_no = frappe.db.get_value("Stock Entry Detail",{"parent" : stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"batch_no")
second_final_item_batch_no = frappe.db.get_value("Stock Entry Detail",{"parent" : stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"batch_no")
asis_final_item_batch_no = frappe.db.get_value("Stock Entry Detail",{"parent" : stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"batch_no")
first_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"TEST_ITEM_1"},"name")
second_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"TEST_ITEM_2"},"name")
third_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"TEST_ITEM_3"},"name")
fourth_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"TEST_ITEM_4"},"name")
final_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"name")
second_final_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"name")
asis_final_stock_ledger_ma_item = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"name")


# # Create Stock Entry for Material Receipt 2 (mr_2)
# from datetime import date,timedelta,datetime
# import datetime
# stock_entry_mr = frappe.new_doc("Stock Entry")
# stock_entry_mr.naming_series = "Test-MR-.###"
# stock_entry_mr.stock_entry_type = "Material Receipt"
# stock_entry_mr.set_posting_time = 1
# stock_entry_mr.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), 1)
# company =  frappe.db.get_value("Company",{},"company_name") 
# warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name")
# stock_entry_mr.to_warehouse = warehouse
# stock_entry_mr.append("items",{
#     "t_warehouse": warehouse,
#     "item_code": "FINISH_TEST_ITEM",
#     "qty": 50,
#     "concentration": 90,
#     "basic_rate": 93,
#     "packing_size": 25,
#     "actual_qty": 50,
#     "actual_valuation_rate":(25*2*(90/100)),
#     "packing_material": packaging_material
# })
# stock_entry_mr.save()
# stock_entry_mr_2_name = stock_entry_mr.name
# stock_entry_mr.submit()
# stock_entry_mr_2_batch_no = frappe.db.get_value("Batch",{"reference_name": stock_entry_mr_2_name},"name")

# # Create Sales Invoice (si)
# from datetime import date,timedelta,datetime
# import datetime

# company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
# warehouse =  frappe.db.get_value("Warehouse",{'company':company, "warehouse_name":"FINISHED GOODS(CRUDE)"},"name") 
# cost_center = frappe.db.get_value("Company",company,"cost_center")

# second_si = frappe.new_doc("Sales Invoice")
# second_si.naming_series = "Test-SALINV-.###"
# second_si.customer = "Test_Customer_1"
# second_si.set_posting_time = 1
# second_si.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), 2)
# second_si.company = company
# second_si.set_warehouse = warehouse
# second_si.update_stock = 1
# second_si.due_date = date.today() + timedelta(10)
# qty = frappe.db.get_value("Batch",final_item_batch_no,"actual_quantity")
# concentration = frappe.db.get_value("Batch",final_item_batch_no,"concentration")
# second_si.append("items",{
#         "item_code":"FINISH_TEST_ITEM",
#         "item_name":"FINISH_TEST_ITEM",
#         "description":"FINISH_TEST_ITEM details",
#         "warehouse": warehouse,
#         "cost_center":cost_center,
#         "qty":qty,
#         "rate":110.00,
#         "concentration": concentration,
#         "batch_no":final_item_batch_no,
#         #"manufacturer":"gg",
#         #"manufacturer_part_no":"gg"
# })
# second_si.save()
# second_si_name = second_si.name
# second_si.submit()
# stock_ledger_second_si = frappe.db.get_value("Stock Ledger Entry",{"voucher_no":second_si_name},"name")


# # Create Stock Entry For Material Issue (mi)
# from datetime import date,timedelta,datetime
# import datetime

# stock_entry_mi = frappe.new_doc("Stock Entry")
# stock_entry_mi.naming_series = "Test-MI-.###"
# stock_entry_mi.stock_entry_type = "Material Issue"
# stock_entry_mi.set_posting_time = 1
# stock_entry_mi.posting_date = frappe.utils.add_days(frappe.utils.nowdate(), 2)
# company =  frappe.db.get_value("Company",{},"company_name") #it will Fetch the First Name of the Company from the list
# warehouse =  frappe.db.get_value("Warehouse",{'company':company,"warehouse_name":"RAW MATERIAL"},"name") 
# stock_entry_mi.from_warehouse = warehouse
# stock_entry_mi.append("items",{
#     "item_code": "TEST_ITEM_3",
#     "qty": 5,
#     "batch_no": second_pr_third_item_batch_no
# })
# stock_entry_mi.save()
# stock_entry_mi_name = stock_entry_mi.name
# stock_entry_mi.submit()

# # 


#Purchase Receipt (pr)
first_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":first_pr_name,"item_code":"TEST_ITEM_1"},"rate")
second_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":second_pr_name,"item_code":"TEST_ITEM_2"},"rate")
third_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":third_pr_name,"item_code":"TEST_ITEM_3"},"rate")
fourth_pr_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":fourth_pr_name,"item_code":"TEST_ITEM_4"},"rate")


first_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":first_pr_name,"item_code":"TEST_ITEM_1"},"qty")
second_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":second_pr_name,"item_code":"TEST_ITEM_2"},"qty")
third_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":third_pr_name,"item_code":"TEST_ITEM_3"},"qty")
fourth_pr_qty = frappe.db.get_value("Purchase Receipt Item",{"parent":fourth_pr_name,"item_code":"TEST_ITEM_4"},"qty")


second_pr_third_item_rate = frappe.db.get_value("Purchase Receipt Item",{"parent":second_pr_name,"item_code":"TEST_ITEM_3"},"rate")

#Stock Ledger Entry for Manufacturing (sl_ma)

first_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_ma_item,"batch_no")
second_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_ma_item,"batch_no")
third_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_ma_item,"batch_no")
fourth_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_ma_item,"batch_no")

final_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",final_stock_ledger_ma_item,"batch_no")
second_final_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",second_final_stock_ledger_ma_item,"batch_no")
asis_final_sl_ma_batch_no = frappe.db.get_value("Stock Ledger Entry",asis_final_stock_ledger_ma_item,"batch_no")

final_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",final_stock_ledger_ma_item,"actual_qty")
second_final_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",second_final_stock_ledger_ma_item,"actual_qty")
asis_final_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",asis_final_stock_ledger_ma_item,"actual_qty")

first_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_ma_item,"actual_qty")
second_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_ma_item,"actual_qty")
third_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_ma_item,"actual_qty")
fourth_sl_ma_qty = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_ma_item,"actual_qty")

final_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",final_stock_ledger_ma_item,"stock_value_difference")
second_final_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",second_final_stock_ledger_ma_item,"stock_value_difference")
asis_final_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",asis_final_stock_ledger_ma_item,"stock_value_difference")

first_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_ma_item,"stock_value_difference")
second_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_ma_item,"stock_value_difference")
third_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_ma_item,"stock_value_difference")
fourth_sl_ma_stock_val_diff = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_ma_item,"stock_value_difference")

final_sl_ma_incoming_rate = frappe.db.get_value("Stock Ledger Entry",final_stock_ledger_ma_item,"incoming_rate")
second_final_sl_ma_incoming_rate = frappe.db.get_value("Stock Ledger Entry",second_final_stock_ledger_ma_item,"incoming_rate")
asis_final_sl_ma_incoming_rate = frappe.db.get_value("Stock Ledger Entry",asis_final_stock_ledger_ma_item,"incoming_rate")

final_sl_ma_valuation_rate = frappe.db.get_value("Stock Ledger Entry",final_stock_ledger_ma_item,"valuation_rate")
second_final_sl_ma_valuation_rate = frappe.db.get_value("Stock Ledger Entry",second_final_stock_ledger_ma_item,"valuation_rate")
asis_final_sl_ma_valuation_rate = frappe.db.get_value("Stock Ledger Entry",asis_final_stock_ledger_ma_item,"valuation_rate")


#Manufacturing (ma)
ma_value_diff = frappe.db.get_value("Stock Entry",stock_entry_ma_name,"value_difference")
ma_total_additional_cost = frappe.db.get_value("Stock Entry",stock_entry_ma_name,"total_additional_costs") 
# if len(ma_doc.additional_costs) == 1:
#     ma_additional_cost = frappe.db.get_value("Landed Cost Taxes and Charges",{"parent":stock_entry_ma_name},"amount")
# elif  > 1:
#     for amt in range(len(ma_doc.additional_costs)):
#         addition += ma_doc.additional_costs[amt].amount
ma_additional_cost = 0
manufacturer_doc = frappe.get_doc("Stock Entry",stock_entry_ma_name)
ma_additional_cost = 0
for amt in range(len(manufacturer_doc.additional_costs)):
    ma_additional_cost += manufacturer_doc.additional_costs[amt].amount


first_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"TEST_ITEM_1"},"qty")
second_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"TEST_ITEM_2"},"qty")
third_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"TEST_ITEM_3"},"qty")
fourth_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"TEST_ITEM_4"},"qty")

final_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"qty")
second_final_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"qty")
asis_final_ma_item_qty = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"qty")

final_ma_item_basic_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"basic_amount")
second_final_ma_item_basic_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"basic_amount")
asis_final_ma_item_basic_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"basic_amount")

final_ma_item_additional_cost = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"additional_cost")
second_final_ma_item_additional_cost = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"additional_cost")
asis_final_ma_item_additional_cost = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"additional_cost")

final_ma_item_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"amount")
second_final_ma_item_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"amount")
asis_final_ma_item_amount = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"amount")

final_ma_item_basic_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"basic_rate")
second_final_ma_item_basic_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"basic_rate")
asis_final_ma_item_basic_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"basic_rate")

final_ma_item_valuation_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"FINISH_TEST_ITEM"},"valuation_rate")
second_final_ma_item_valuation_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"valuation_rate")
asis_final_ma_item_valuation_rate = frappe.db.get_value("Stock Entry Detail",{"parent":stock_entry_ma_name,"item_code":"AsIs_Finish_item"},"valuation_rate")

ma_total_incoming_value =  frappe.db.get_value("Stock Entry",stock_entry_ma_name,"total_incoming_value")
ma_total_outgoing_value = frappe.db.get_value("Stock Entry",stock_entry_ma_name,"total_outgoing_value")

# Work order

final_wo_bom_cost_ratio = frappe.db.get_value("Work Order Finish Item",{"parent":work_name,"item_code":"FINISH_TEST_ITEM"},"bom_cost_ratio")
second_final_wo_bom_cost_ratio = frappe.db.get_value("Work Order Finish Item",{"parent":work_name,"item_code":"SECOND_FINISH_TEST_ITEM"},"bom_cost_ratio")
asis_final_wo_bom_cost_ratio = frappe.db.get_value("Work Order Finish Item",{"parent":work_name,"item_code":"AsIs_Finish_item"},"bom_cost_ratio")


#Stock Ledger Entry for purchase receipt (sl_pr)
first_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"incoming_rate")
second_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"incoming_rate")
third_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"incoming_rate")
fourth_sl_pr_incoming_rate = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_pr_name,"incoming_rate")

first_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"actual_qty")
second_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"actual_qty")
third_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"actual_qty")
fourth_sl_pr_qty = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_pr_name,"actual_qty")

first_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_pr_name,"batch_no")
second_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_pr_name,"batch_no")
third_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_pr_name,"batch_no")
fourth_sl_pr_batch_no = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_pr_name,"batch_no")

#Stock Ledger Entry for Material Transfer (sl_mtm)
first_sl_mtm_incoming_rate = frappe.db.get_value("Stock Ledger Entry",first_stock_ledger_mtm_item_name,"incoming_rate")
second_sl_mtm_incoming_rate = frappe.db.get_value("Stock Ledger Entry",second_stock_ledger_mtm_item_name,"incoming_rate")
third_sl_mtm_incoming_rate = frappe.db.get_value("Stock Ledger Entry",third_stock_ledger_mtm_item_name,"incoming_rate")
fourth_sl_mtm_incoming_rate = frappe.db.get_value("Stock Ledger Entry",fourth_stock_ledger_mtm_item_name,"incoming_rate")

mtm_value_diff = frappe.db.get_value("Stock Entry",stock_entry_mtm_name,"value_difference")


msg = "PR1: Incoming Rate Doesn't Match"
assert first_pr_rate == first_sl_pr_incoming_rate,msg
#self.assertEqual(first_pr_rate,first_sl_pr_incoming_rate,msg="PR1: Incoming Rate Doesn't Match")

msg = "PR1: Quantity Doesn't Match"
assert first_pr_qty == first_sl_pr_qty,msg
#self.assertEqual(first_pr_qty,first_sl_pr_qty,msg="PR1: Quantity Doesn't Match")

msg="PR1: Batch ID Doesn't Match"
assert first_pr_batch_no == first_sl_pr_batch_no,msg
#self.assertEqual(first_pr_batch_no,first_sl_pr_batch_no,msg="PR1: Batch ID Doesn't Match")


msg="PR2: Incoming Rate Doesn't Match"
assert second_pr_rate == second_sl_pr_incoming_rate,msg
#self.assertEqual(second_pr_rate,second_sl_pr_incoming_rate,msg="PR2: Incoming Rate Doesn't Match")

msg="PR2: Quantity Doesn't Match"
assert second_pr_qty == second_sl_pr_qty,msg
#self.assertEqual(second_pr_qty,second_sl_pr_qty,msg="PR2: Quantity Doesn't Match")

msg="PR2: Batch ID Doesn't Match"
assert second_pr_batch_no == second_sl_pr_batch_no,msg
#self.assertEqual(second_pr_batch_no,second_sl_pr_batch_no,msg="PR2: Batch ID Doesn't Match")

msg="PR3: Incoming Rate Doesn't Match"
assert third_pr_rate == third_sl_pr_incoming_rate,msg
#self.assertEqual(third_pr_rate,third_sl_pr_incoming_rate,msg="PR3: Incoming Rate Doesn't Match")

msg="PR3: Quantity Doesn't Match"
assert third_pr_qty == third_sl_pr_qty,msg
#self.assertEqual(third_pr_qty,third_sl_pr_qty,msg="PR3: Quantity Doesn't Match")

msg="PR3: Batch ID Doesn't Match"
assert third_pr_batch_no == third_sl_pr_batch_no,msg
#self.assertEqual(third_pr_batch_no,third_sl_pr_batch_no,msg="PR3: Batch ID Doesn't Match")

msg="PR4: Incoming Rate Doesn't Match"
assert fourth_pr_rate == round(fourth_sl_pr_incoming_rate,1),msg
#self.assertEqual(fourth_pr_rate,fourth_sl_pr_incoming_rate,msg="PR4: Incoming Rate Doesn't Match")

msg="PR4: Quantity Doesn't Match"
assert fourth_pr_qty == fourth_sl_pr_qty,msg
#self.assertEqual(fourth_pr_qty,fourth_sl_pr_qty,msg="PR4: Quantity Doesn't Match")

msg="PR4: Batch ID Doesn't Match"
assert fourth_pr_batch_no == fourth_sl_pr_batch_no,msg
#self.assertEqual(fourth_pr_batch_no,fourth_sl_pr_batch_no,msg="PR4: Batch ID Doesn't Match")

msg="MTM1: Incoming Rate Doesn't Match"
assert first_pr_rate == first_sl_mtm_incoming_rate,msg
#self.assertEqual(first_pr_rate,first_sl_mtm_incoming_rate,msg="MTM1: Incoming Rate Doesn't Match")

msg="MTM2: Incoming Rate Doesn't Match"
assert second_pr_rate == second_sl_mtm_incoming_rate,msg
#self.assertEqual(second_pr_rate,second_sl_mtm_incoming_rate,msg="MTM2: Incoming Rate Doesn't Match")

msg="MTM3: Incoming Rate Doesn't Match"
assert third_pr_rate == third_sl_mtm_incoming_rate,msg
#self.assertEqual(third_pr_rate,third_sl_mtm_incoming_rate,msg="MTM3: Incoming Rate Doesn't Match")

msg="MTM4: Incoming Rate Doesn't Match"
assert fourth_pr_rate == fourth_sl_mtm_incoming_rate,msg
#self.assertEqual(fourth_pr_rate,fourth_sl_mtm_incoming_rate,msg="MTM3: Incoming Rate Doesn't Match")

msg="MTM: There is Value difference"
assert mtm_value_diff == 0 ,msg

msg="MA: Total additional cost doesn't Match with sum of Additional Cost"
assert ma_total_additional_cost == ma_additional_cost,msg

msg="MA: Total Value difference doesn't Match"
assert ma_total_additional_cost == ma_value_diff,msg
#self.assertEqual(ma_total_additional_cost,ma_value_diff,msg="MA: Total Value difference doesn't Match")

msg="MA1: Batch No doesn't Match"
assert first_sl_ma_batch_no == first_pr_batch_no,msg
#self.assertEqual(first_sl_ma_batch_no,first_pr_batch_no,msg="MA1: Batch No doesn't Match")

msg="MA2: Batch No doesn't Match"
assert second_sl_ma_batch_no == second_pr_batch_no,msg
#self.assertEqual(second_sl_ma_batch_no,second_pr_batch_no,msg="MA2: Batch No doesn't Match")

msg="MA3: Batch No doesn't Match"
assert third_sl_ma_batch_no == third_pr_batch_no,msg
#self.assertEqual(third_sl_ma_batch_no,third_pr_batch_no,msg="MA3: Batch No doesn't Match")

msg="MA4: Batch No doesn't Match"
assert fourth_sl_ma_batch_no == fourth_pr_batch_no,msg
#self.assertEqual(fourth_sl_ma_batch_no,fourth_pr_batch_no,msg="MA3: Batch No doesn't Match")

msg="MAFinal: Quantity doesn't Match"
assert final_sl_ma_qty == final_ma_item_qty,msg

msg="MASecondFinal: Quantity doesn't Match"
assert second_final_sl_ma_qty == second_final_ma_item_qty,msg

msg="MAAsIsFinal: Quantity doesn't Match"
assert round(asis_final_sl_ma_qty,2) == round(asis_final_ma_item_qty,2),msg

msg="MAFinal: Valuation Rate doesn't Match"
assert final_sl_ma_valuation_rate == final_ma_item_valuation_rate,msg

msg="MASecondFinal: Valuation Rate doesn't Match"
assert second_final_sl_ma_valuation_rate == second_final_ma_item_valuation_rate,msg

msg="MAAsIsFinal: Valuation Rate doesn't Match"
assert asis_final_sl_ma_valuation_rate == asis_final_ma_item_valuation_rate,msg

msg="MAFinal: Batch No doesn't Match"
assert final_sl_ma_batch_no == final_item_batch_no,msg

msg="MASecond_Final: Batch No doesn't Match"
assert second_final_sl_ma_batch_no == second_final_item_batch_no,msg

msg="MAAsIs: Batch No doesn't Match"
assert asis_final_sl_ma_batch_no == asis_final_item_batch_no,msg

msg="MA1: Incoming Rate doesn't Match"
if first_sl_ma_qty < 0:
    first_sl_ma_incoming_rate = round(first_sl_ma_stock_val_diff) / first_sl_ma_qty
    assert first_sl_ma_incoming_rate == first_pr_rate,msg
    #self.assertEqual(abs(first_sl_ma_qty),first_ma_item_qty,msg="MA1: Quantity doesn't Match")
else:
    frappe.msgprint(("MA1:Quantity should be < 0"))

msg="MA2: Incoming Rate doesn't Match"
if second_sl_ma_qty < 0:
    second_sl_ma_incoming_rate = round(second_sl_ma_stock_val_diff) / second_sl_ma_qty
    assert second_sl_ma_incoming_rate == second_pr_rate,msg
    #self.assertEqual(abs(second_sl_ma_qty),second_ma_item_qty,msg="MA2: Quantity doesn't Match")
else:
    frappe.msgprint(("MA2:Quantity should be < 0"))

msg="MA3: Incoming Rate doesn't Match"
if third_sl_ma_qty < 0:
    third_sl_ma_incoming_rate = round(third_sl_ma_stock_val_diff) / third_sl_ma_qty
    assert third_sl_ma_incoming_rate == third_pr_rate,msg
    #self.assertEqual(abs(third_sl_ma_qty),third_ma_item_qty,msg="MA3: Quantity doesn't Match")
else:
    frappe.msgprint(("MA3:Quantity should be < 0"))

msg="MA4: Incoming Rate doesn't Match"
if fourth_sl_ma_qty < 0:
    fourth_sl_ma_incoming_rate = (round(fourth_sl_ma_stock_val_diff )/ fourth_sl_ma_qty)
    assert round(fourth_sl_ma_incoming_rate,1) == fourth_pr_rate,msg
    #self.assertEqual(abs(fourth_sl_ma_qty),fourth_ma_item_qty,msg="MA4: Quantity doesn't Match")
else:
    frappe.msgprint(("MA4:Quantity should be < 0"))

msg="MAFinal: Incoming Rate doesn't Match"
assert (round(final_sl_ma_stock_val_diff )/ final_sl_ma_qty) == round(final_sl_ma_incoming_rate,2),msg

msg="MASecondFinal: Incoming Rate doesn't Match"
assert round(second_final_sl_ma_stock_val_diff / second_final_sl_ma_qty,2) == round(second_final_sl_ma_incoming_rate,2),msg

msg="MAAsIs: Incoming Rate doesn't Match"
assert round(asis_final_sl_ma_stock_val_diff/ asis_final_sl_ma_qty,2) == round(asis_final_sl_ma_incoming_rate,2),msg


msg="MA: total outgoing value doesn't match with sum of total incoming value and total value difference"
assert ma_total_incoming_value == ma_total_outgoing_value + ma_value_diff,msg
#self.assertEqual(ma_total_outgoing_value,ma_total_incoming_value+ma_value_diff)

# msg = "MA: Valuation Rate doesn't Match"
# ma_valuation_rate = flt(round(ma_total_incoming_value,1)/flt(final_ma_item_qty))
# assert ma_valuation_rate == final_ma_item_valuation_rate,msg

msg = "MAFinal: Basic Amount doesn't Match"
assert round(final_ma_item_basic_amount,1) == round(flt(ma_total_outgoing_value * final_wo_bom_cost_ratio / 100),1),msg

msg = "MAFinal: Additional Cost doesn't Match"
assert final_ma_item_additional_cost == flt(ma_total_additional_cost * final_wo_bom_cost_ratio / 100),msg

msg = "MAFinal: Amount doesn't Match"
assert round(final_ma_item_amount,1) == round(final_ma_item_basic_amount + final_ma_item_additional_cost,1),msg

msg = "MAFinal: Basic Rate doesn't Match"
assert round(final_ma_item_basic_rate,2) == round(flt(final_ma_item_basic_amount/ final_ma_item_qty),2),msg

msg = "MAFinal: Valuation Rate doesn't Match"
assert round(final_ma_item_valuation_rate,2) == round(flt(final_ma_item_amount/ final_ma_item_qty),2),msg

msg = "MASecondFinal: Basic Amount doesn't Match"
assert round(second_final_ma_item_basic_amount,1) == round(flt(ma_total_outgoing_value * second_final_wo_bom_cost_ratio / 100),1),msg

msg = "MASecondFinal: Additional Cost doesn't Match"
assert round(second_final_ma_item_additional_cost,1) == round(flt(ma_total_additional_cost * second_final_wo_bom_cost_ratio / 100),1),msg

msg = "MASecondFinal: Amount doesn't Match"
assert round(second_final_ma_item_amount,1) == round(second_final_ma_item_basic_amount + second_final_ma_item_additional_cost,1),msg

msg = "MASecondFinal: Basic Rate doesn't Match"
assert round(second_final_ma_item_basic_rate,2) == round(flt(second_final_ma_item_basic_amount/ second_final_ma_item_qty),2),msg

msg = "MASecondFinal: Valuation Rate doesn't Match"
assert round(second_final_ma_item_valuation_rate,2) == round(flt(second_final_ma_item_amount/ second_final_ma_item_qty),2),msg

msg = "MAAsIsFInal: Basic Amount doesn't Match"
assert round(asis_final_ma_item_basic_amount,1) == round(flt(ma_total_outgoing_value * asis_final_wo_bom_cost_ratio / 100),1),msg

msg = "MAAsIsFInal: Additional Cost doesn't Match"
assert round(asis_final_ma_item_additional_cost,1) == round(flt(ma_total_additional_cost * asis_final_wo_bom_cost_ratio / 100),1),msg

msg = "MAAsIsFinal: Amount doesn't Match"
assert round(asis_final_ma_item_amount,1) == round(asis_final_ma_item_basic_amount + asis_final_ma_item_additional_cost,1),msg

msg = "MAAsIsFinal: Basic Rate doesn't Match"
assert round(asis_final_ma_item_basic_rate,2) == round(asis_final_ma_item_basic_amount/ asis_final_ma_item_qty,2),msg

msg = "MAAsIsFinal: Valuation Rate doesn't Match"
assert round(asis_final_ma_item_valuation_rate,2) == round(asis_final_ma_item_amount/ asis_final_ma_item_qty,2),msg


# material_issue_delete = frappe.get_doc("Stock Entry",stock_entry_mi_name)
# material_issue_delete.cancel()
# material_issue_delete.delete()
# 


# sales_invoice_delete = frappe.get_doc("Sales Invoice",second_si_name)
# sales_invoice_delete.cancel()
# sales_invoice_delete.delete()
# 


# frappe.db.set_value("Batch",stock_entry_mr_2_batch_no,"reference_name","")
# 

# material_receipt_2_delete = frappe.get_doc("Stock Entry",stock_entry_mr_2_name)
# material_receipt_2_delete.flags.ignore_links = True
# material_receipt_2_delete.cancel()
# material_receipt_2_delete.delete()
# 

# batch_material_receipt_2_delete = frappe.get_doc("Batch",stock_entry_mr_2_batch_no)
# batch_material_receipt_2_delete.delete()
# 

frappe.db.set_value("Batch",final_item_batch_no,"reference_name","")

manufacture_delete = frappe.get_doc("Stock Entry",stock_entry_ma_name)
manufacture_delete.flags.ignore_links = True
manufacture_delete.cancel()
manufacture_delete.delete()


batch_manufacture_delete = frappe.get_doc("Batch",final_item_batch_no)
batch_manufacture_delete.delete()


# frappe.db.set_value("Batch",stock_entry_mr_1_batch_no,"reference_name","")
# 

# material_receipt_1_delete = frappe.get_doc("Stock Entry",stock_entry_mr_1_name)
# material_receipt_1_delete.flags.ignore_links = True
# material_receipt_1_delete.cancel()
# material_receipt_1_delete.delete()
# 

# batch_material_receipt_1_delete = frappe.get_doc("Batch",stock_entry_mr_1_batch_no)
# batch_material_receipt_1_delete.delete()
# 

material_transfer_delete = frappe.get_doc("Stock Entry",stock_entry_mtm_name)
material_transfer_delete.flags.ignore_links = True
material_transfer_delete.cancel()
material_transfer_delete.delete()

work_order_delete = frappe.get_doc("Work Order",work_name)
work_order_delete.flags.ignore_links = True
work_order_delete.cancel()
work_order_delete.delete()

bom_delete = frappe.get_doc("BOM",bom_name)
bom_delete.cancel()
bom_delete.delete()

bom2_delete = frappe.get_doc("BOM",bom2_name)
bom2_delete.cancel()
bom2_delete.delete()

bom3_delete = frappe.get_doc("BOM",bom3_name)
bom3_delete.cancel()
bom3_delete.delete()

fourth_pr = frappe.get_doc("Purchase Receipt",fourth_pr_name)
third_pr = frappe.get_doc("Purchase Receipt",third_pr_name)
second_pr = frappe.get_doc("Purchase Receipt",second_pr_name)
first_pr = frappe.get_doc("Purchase Receipt",first_pr_name)

fourth_pr.ignore_mandatory = True
fourth_pr.ignore_links = True
fourth_pr.cancel()
fourth_pr.delete()

third_pr.ignore_mandatory = True
third_pr.ignore_links = True
third_pr.cancel()
third_pr.delete()

second_pr.cancel()
second_pr.delete()

first_pr.cancel()
first_pr.delete()

item_delete_1 = frappe.get_doc("Item","TEST_ITEM_1")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"TEST_ITEM_1"},"name"):
    item_delete_1.delete()
else:
    frappe.msgprint("test item 1 doc is linked with purchase receipt or sales invoice or BIN")

item_delete_2 = frappe.get_doc("Item","TEST_ITEM_2")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"TEST_ITEM_2"},"name"):
    item_delete_2.delete()
else:
    frappe.msgprint("test item 2 doc is linked with purchase receipt or sales invoice or BIN")

item_delete_3 = frappe.get_doc("Item","TEST_ITEM_3")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"TEST_ITEM_3"},"name"):
    item_delete_3.delete()
else:
    frappe.msgprint("test item 3 doc is linked with purchase receipt or sales invoice or BIN")

item_delete_4 = frappe.get_doc("Item","TEST_ITEM_4")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"TEST_ITEM_4"},"name"):
    item_delete_4.delete()
else:
    frappe.msgprint("test item 4 doc is linked with purchase receipt or sales invoice or BIN")


item_delete_finish = frappe.get_doc("Item","FINISH_TEST_ITEM")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"FINISH_TEST_ITEM"},"name"):
    item_delete_finish.delete()
else:
    frappe.msgprint("test item finish doc is linked with purchase receipt or sales invoice or BIN")

item_delete_second_finish = frappe.get_doc("Item","SECOND_FINISH_TEST_ITEM")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"SECOND_FINISH_TEST_ITEM"},"name"):
    item_delete_second_finish.delete()
else:
    frappe.msgprint("test item finish doc is linked with purchase receipt or sales invoice or BIN")

item_delete_asis_finish = frappe.get_doc("Item","AsIs_Finish_item")
if frappe.db.get_value("Bin",{"actual_qty":0,"stock_value":0,"item_code":"AsIs_Finish_item"},"name"):
    item_delete_asis_finish.delete()
else:
    frappe.msgprint("test item finish doc is linked with purchase receipt or sales invoice or BIN")


supplier_delete = frappe.get_doc("Supplier","Test_Supplier_1")
supplier_delete.delete()
customer_delete = frappe.get_doc("Customer","Test_Customer_1")
customer_delete.delete() 




