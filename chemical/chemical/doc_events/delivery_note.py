import frappe
from frappe import msgprint, _
from frappe.utils import flt, cint
from chemical.api import cal_rate_qty, quantity_price_to_qty_rate

def onload(self,method):
    quantity_price_to_qty_rate(self)

def validate(self,method):
    cal_rate_qty(self)
	
def dn_on_submit(self, method):
	update_sales_invoice(self)
	validate_customer_batch(self)
#added
def on_submit(self, method):
	update_sales_invoice(self)

def before_cancel(self, method):
	dn_update_status_updater_args(self)
	update_sales_invoice(self)

def before_submit(self, method):
	dn_update_status_updater_args(self)


def update_sales_invoice(self):
	for row in self.items:
		if row.against_sales_invoice and row.si_detail:
			if self._action == 'submit':
				delivery_note = self.name
				dn_detail = row.name

			elif self._action == 'cancel':
				delivery_note = ''
				dn_detail = ''

			frappe.db.sql("""update `tabSales Invoice Item` 
				set dn_detail = %s, delivery_note = %s 
				where name = %s """, (dn_detail, delivery_note, row.si_detail))

def dn_update_status_updater_args(self):
	self.status_updater = [{
		'source_dt': 'Delivery Note Item',
		'target_dt': 'Sales Order Item',
		'join_field': 'so_detail',
		'target_field': 'delivered_qty', # In Sales Order Item
		'target_parent_dt': 'Sales Order',
		'target_parent_field': 'per_delivered',
		'target_ref_field': 'quantity', # In Sales Order Item
		'source_field': 'quantity', # In Delivery Note Item
		'percent_join_field': 'against_sales_order',
		'status_field': 'delivery_status',
		'keyword': 'Delivered',
		'second_source_dt': 'Sales Invoice Item',
		'second_source_field': 'quantity', # In Sales Invoice Item
		'second_join_field': 'so_detail',
		'overflow_type': 'delivery',
		'second_source_extra_cond': """ and exists(select name from `tabSales Invoice`
			where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
	},
	{
		'source_dt': 'Delivery Note Item',
		'target_dt': 'Sales Invoice Item',
		'join_field': 'si_detail',
		'target_field': 'delivered_qty',
		'target_parent_dt': 'Sales Invoice',
		'target_ref_field': 'quantity', # In Sales Invoice Item
		'source_field': 'quantity', # In Delivery Note Item
		'percent_join_field': 'against_sales_invoice',
		'overflow_type': 'delivery',
		'no_allowance': 1
	}]

	if cint(self.is_return):
		self.status_updater.append({
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Order Item',
			'join_field': 'so_detail',
			'target_field': 'returned_qty',
			'target_parent_dt': 'Sales Order',
			'source_field': '-1 * quantity',
			'second_source_dt': 'Sales Invoice Item',
			'second_source_field': '-1 * quantity',
			'second_join_field': 'so_detail',
			'extra_cond': """ and exists (select name from `tabDelivery Note`
				where name=`tabDelivery Note Item`.parent and is_return=1)""",
			'second_source_extra_cond': """ and exists (select name from `tabSales Invoice`
				where name=`tabSales Invoice Item`.parent and is_return=1 and update_stock=1)"""
		})


def validate_customer_batch(self):
	for row in self.items:
		if row.batch_no:
			batch_customer = frappe.db.get_value("Batch",row.batch_no,"customer")
			if batch_customer:
				if batch_customer != self.customer:
					frappe.throw(_("Please select correct batch for customer <strong>{}</strong> in row {}".format(self.customer,row.idx)))


