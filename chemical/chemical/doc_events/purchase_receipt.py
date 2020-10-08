import frappe
from frappe.utils import flt, cint
from chemical.api import purchase_cal_rate_qty, quantity_price_to_qty_rate
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
import re

def onload(self,method):
	quantity_price_to_qty_rate(self)

def before_validate(self,method):
	purchase_cal_rate_qty(self)

def before_save(self,method):
	rename_po(self)
		
def before_submit(self, method):
	pr_update_status_updater_args(self)

def before_cancel(self, method):
	pr_update_status_updater_args(self)
	PurchaseReceipt.delete_auto_created_batches = delete_auto_created_batches

def t_validate(self,method):
	cal_total(self)

def pr_update_status_updater_args(self):
	self.status_updater = [{
		'source_dt': 'Purchase Receipt Item',
		'target_dt': 'Purchase Order Item',
		'join_field': 'purchase_order_item',
		'target_field': 'received_qty', # In Purchase Order Item
		'target_parent_dt': 'Purchase Order',
		'target_parent_field': 'per_received',
		'target_ref_field': 'quantity', # In Purchase Order Item
		'source_field': 'quantity', #In Purchase Receipt Item
		'percent_join_field': 'purchase_order',
		'second_source_dt': 'Purchase Invoice Item',
		'second_source_field': 'quantity',  # In Purchase Invoice Item
		'second_join_field': 'po_detail',
		'overflow_type': 'receipt',
		'second_source_extra_cond': """ and exists(select name from `tabPurchase Invoice`
			where name=`tabPurchase Invoice Item`.parent and update_stock = 1)"""
	},
	{
		'source_dt': 'Purchase Receipt Item',
		'target_dt': 'Material Request Item',
		'join_field': 'material_request_item',
		'target_field': 'received_qty',
		'target_parent_dt': 'Material Request',
		'target_parent_field': 'per_received',
		'target_ref_field': 'quantity',
		'source_field': 'quantity',
		'percent_join_field': 'material_request'
	}]

	if cint(self.is_return):
		self.status_updater.append({
			'source_dt': 'Purchase Receipt Item',
			'target_dt': 'Purchase Order Item',
			'join_field': 'purchase_order_item',
			'target_field': 'returned_qty',
			'source_field': '-1 * quantity',
			'second_source_dt': 'Purchase Invoice Item',
			'second_source_field': '-1 * quantity',
			'second_join_field': 'po_detail',
			'extra_cond': """ and exists (select name from `tabPurchase Receipt`
				where name=`tabPurchase Receipt Item`.parent and is_return=1)""",
			'second_source_extra_cond': """ and exists (select name from `tabPurchase Invoice`
				where name=`tabPurchase Invoice Item`.parent and is_return=1 and update_stock=1)"""
		})
	# self.update_qty()
def cal_total(self):
	total_quantity = 0
	total_supplier_qty=0
	total_supplier_quantity = 0
	total_packages = 0
	for d in self.items:
		total_quantity = total_quantity + flt(d.quantity)
		total_supplier_qty = total_supplier_qty + flt(d.supplier_qty)
		total_supplier_quantity = total_supplier_quantity + flt(d.supplier_quantity)
		total_packages = total_packages + (d.no_of_packages)
	
	self.total_quantity = total_quantity
	self.total_supplier_qty = total_supplier_qty
	self.total_supplier_quantity = total_supplier_quantity
	self.total_packages = total_packages

def delete_auto_created_batches(self):
	pass

@frappe.whitelist()
def rename_po(existing_name, series_value):
	new_name = re.findall("^(.*[\\\/])",existing_name)[0] # Before Slash
	last_digits = re.findall("[^\/]+$",existing_name)[0] # After Slash
	len_last_digits = len(last_digits) # After Slash
	if series_value:
		if len(series_value) > 4:
			frappe.throw("Please Enter 4 Digit Series Value")
		temp_digits = last_digits.replace(last_digits,series_value)
		if len(temp_digits)!=4:
			temp_digits = temp_digits.rjust((4-len(temp_digits)) + len(temp_digits),'0')
		new_name += temp_digits
		if new_name != existing_name:
			frappe.rename_doc("Purchase Receipt", existing_name, new_name, force=True)
			frappe.db.set_value("Purchase Receipt",new_name,"series_value",series_value)
			return new_name
			#last_digits.replace(last_digits[-(len(series_value)):],series_value) 
	# last_3_digit_remove = str(existing_name[:-4])
	# len_after_slash = len(re.findall("[^\/]+$",existing_name)[0])
	# new_name = ""
	# if series_value and len_after_slash == 3:
	# 	if len(series_value) > 4:
	# 		frappe.throw("Please Enter 4 Digit Series Value")
	# 	last_3_digit_remove += "/"
	# 	len_series_value = len(str(series_value))
	# 	if len_series_value == 1:
	# 		new_name = last_3_digit_remove + "00" + str(series_value)
	# 	elif len_series_value == 2:
	# 		new_name = last_3_digit_remove + "0" + str(series_value)
	# 	elif len_series_value == 3 or len_series_value == 4:
	# 		new_name = last_3_digit_remove + str(series_value)
		# if new_name != existing_name:
		# 	frappe.rename_doc("Purchase Receipt", existing_name, new_name, force=True)
		# 	frappe.db.set_value("Purchase Receipt",new_name,"series_value",series_value)
		# 	return new_name

	# elif series_value:
	# 	if len(series_value) > 4:
	# 		frappe.throw("Please Enter 4 Digit Series Value")
	# 	len_series_value = len(str(series_value))
	# 	if len_series_value == 1:
	# 		new_name = last_3_digit_remove + "000" + str(series_value)
	# 	elif len_series_value == 2:
	# 		new_name = last_3_digit_remove + "00" + str(series_value)
	# 	elif len_series_value == 3:
	# 		new_name = last_3_digit_remove + "0" +  str(series_value)
	# 	elif len_series_value == 4:
	# 		new_name = last_3_digit_remove + str(series_value)
				
	# 	if new_name != existing_name:
	# 		frappe.rename_doc("Purchase Receipt", existing_name, new_name, force=True)
	# 		frappe.db.set_value("Purchase Receipt",new_name,"series_value",series_value)
	# 		return new_name
		

# def pr_update_default_status_updater_args(self):
# 	self.status_updater = [{
# 		'source_dt': 'Purchase Receipt Item',
# 		'target_dt': 'Purchase Order Item',
# 		'join_field': 'purchase_order_item',
# 		'target_field': 'received_qty',
# 		'target_parent_dt': 'Purchase Order',
# 		'target_ref_field': 'qty',
# 		'source_field': 'received_qty',
# 		'percent_join_field': 'purchase_order',
# 		'second_source_dt': 'Purchase Invoice Item',
# 		'second_source_field': 'received_qty',
# 		'second_join_field': 'po_detail',
# 		'overflow_type': 'receipt',
# 		'second_source_extra_cond': """ and exists(select name from `tabPurchase Invoice`
# 			where name=`tabPurchase Invoice Item`.parent and update_stock = 1)"""
# 	},
# 	{
# 		'source_dt': 'Purchase Receipt Item',
# 		'target_dt': 'Material Request Item',
# 		'join_field': 'material_request_item',
# 		'target_field': 'received_qty',
# 		'target_parent_dt': 'Material Request',
# 		'target_parent_field': 'per_received',
# 		'target_ref_field': 'qty',
# 		'source_field': 'qty',
# 		'percent_join_field': 'material_request'
# 	}]

# 	if cint(self.is_return):
# 		self.status_updater.append({
# 			'source_dt': 'Purchase Receipt Item',
# 			'target_dt': 'Purchase Order Item',
# 			'join_field': 'purchase_order_item',
# 			'target_field': 'returned_qty',
# 			'source_field': '-1 * qty',
# 			'second_source_dt': 'Purchase Invoice Item',
# 			'second_source_field': '-1 * qty',
# 			'second_join_field': 'po_detail',
# 			'extra_cond': """ and exists (select name from `tabPurchase Receipt`
# 				where name=`tabPurchase Receipt Item`.parent and is_return=1)""",
# 			'second_source_extra_cond': """ and exists (select name from `tabPurchase Invoice`
# 				where name=`tabPurchase Invoice Item`.parent and is_return=1 and update_stock=1)"""
# 		})

# 	self.update_qty()
