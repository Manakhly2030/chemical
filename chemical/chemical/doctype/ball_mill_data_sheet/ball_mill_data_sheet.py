# -*- coding: utf-8 -*-
# Copyright (c) 2018, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowtime, flt, cint, getdate, get_fullname, get_url_to_form
from erpnext.stock.utils import get_incoming_rate
from erpnext.stock.stock_ledger import get_valuation_rate
from frappe.model.mapper import get_mapped_doc
from finbyzerp.api import get_fiscal, naming_series_name
import datetime

class BallMillDataSheet(Document):

	def before_naming(self):
		if not self.get('amended_from') and not self.get('name'):
			date = self.get("date") or getdate()
			fiscal = get_fiscal(date)
			self.fiscal = fiscal
			if not self.get('company_series'):
				self.company_series = None
			if self.get('series_value'):
				if self.series_value > 0:
					name = naming_series_name(self.naming_series, fiscal, self.company_series)
					check = frappe.db.get_value('Series', name, 'current', order_by="name")
					if check == 0:
						pass
					elif not check:
						frappe.db.sql("insert into tabSeries (name, current) values ('{}', 0)".format(name))

					frappe.db.sql("update `tabSeries` set current = {} where name = '{}'".format(cint(self.series_value) - 1, name))


	def validate(self):
		self.set_incoming_rate()
		self.repack_calculation()
		self.cal_total()
		if self._action == 'submit':
			self.validate_qty()

	def set_incoming_rate(self):
		precision = cint(frappe.db.get_default("float_precision")) 
		for d in self.items:
			if d.source_warehouse:
				args = self.get_args_for_incoming_rate(d)
				d.basic_rate = flt(get_incoming_rate(args), precision)
			elif not d.source_warehouse:
				d.basic_rate = 0.0
			elif self.warehouse and not d.basic_rate:
				d.basic_rate = flt(get_valuation_rate(d.item_code, self.warehouse,
					self.doctype, d.name, 1,
					currency=erpnext.get_company_currency(self.company)), precision)

			d.basic_amount = d.basic_rate * d.qty
	
	
	def get_args_for_incoming_rate(self, item):
		warehouse = item.source_warehouse or self.warehouse
		return frappe._dict({
			"item_code": item.item_name,
			"warehouse": warehouse,
			"posting_date": self.date,
			"posting_time": nowtime(),
			"qty": warehouse and -1*flt(item.quantity) or flt(item.quantity),
			"voucher_type": self.doctype,
			"voucher_no": item.name,
			"company": self.company,
			"allow_zero_valuation": 1,
			"batch_no":item.batch_no
		})
	def repack_calculation(self):
		for d in self.items:
			maintain_as_is_stock = frappe.db.get_value("Item",d.item_name,'maintain_as_is_stock')

			concentration = d.concentration or 100

			if d.get('packing_size') and d.get('no_of_packages'):
				d.qty = (d.packing_size * d.no_of_packages)

				if maintain_as_is_stock:
					d.quantity = flt(d.qty) * flt(concentration) / 100
					d.price = flt(d.basic_rate) * 100 / flt(concentration)

				else:
					d.quantity = flt(d.qty)
					d.price = flt(d.basic_rate)

			else:
				if maintain_as_is_stock:
					d.price = flt(d.basic_rate)*100/flt(concentration)

					if d.quantity:
						d.qty = flt((d.quantity * 100.0) / flt(concentration))

					if d.qty and not d.quantity:
						d.quantity = flt(d.qty) * flt(concentration) / 100.0
				else:
					d.price = flt(d.basic_rate)

					if d.quantity:
						d.qty = flt(d.quantity)

					if d.qty and not d.quantity:
						d.quantity = flt(d.qty)
		
		for d in self.packaging:
			maintain_as_is_stock = frappe.db.get_value("Item",self.product_name,'maintain_as_is_stock')
			if d.get('packing_size') and d.get('no_of_packages'):
				d.qty = d.packing_size * d.no_of_packages
				if maintain_as_is_stock:
					if d.qty:
						d.quantity = flt(d.qty) * flt(d.concentration) / 100.0

				else:
					if d.qty:
						d.quantity = flt(d.qty)
			else:
				if maintain_as_is_stock:
					if d.qty:
						d.quantity = flt(d.qty) * flt(d.concentration) / 100.0
					
					if d.quantity and not d.qty:
						d.qty = flt(d.quantity) * 100 / flt(d.concentration)

				else:
					if d.qty:
						d.quantity = flt(d.qty)				

					if d.quantity and not d.qty:
						d.qty = flt(d.quantity)
	
	def on_submit(self):
		if self.get('create_stock_entry') == 0:
			create_stock_entry = 0
		else:
			create_stock_entry = 1
		if create_stock_entry:
			se = frappe.new_doc("Stock Entry")
			se.purpose = "Repack"
			se.company = self.company
			se.stock_entry_type = "Repack"
			se.set_posting_time = 1
			se.posting_date = self.date
			se.posting_time = self.posting_time
			se.from_ball_mill = 1
			cost_center = frappe.db.get_value("Company",self.company,"cost_center")
			if hasattr(self,'send_to_party'):
				se.send_to_party = self.send_to_party
			if hasattr(self,'party_type'):
				se.party_type = self.party_type
			if hasattr(self,'party'):
				se.party = self.party

			for row in self.items:
				se.append('items',{
					'item_code': row.item_name,
					's_warehouse': row.source_warehouse,
					'qty': row.qty,
					'quantity':row.quantity,
					'basic_rate': row.basic_rate,
					'price':row.price,
					'basic_amount': row.basic_amount,
					'cost_center': cost_center,
					'batch_no': row.batch_no,
					'concentration':row.concentration,
					'packaging_material':row.packaging_material,
					'packing_size':row.packing_size,
					'no_of_packages':row.no_of_packages
				})

			for d in self.packaging:	
				se.append('items',{
					'item_code': self.product_name,
					't_warehouse': d.warehouse or self.warehouse,
					'qty': d.qty,
					'quantity':d.quantity,
					'packaging_material': d.packaging_material,
					'packing_size': d.packing_size,
					'no_of_packages': d.no_of_packages,
					'lot_no': d.lot_no,
					'concentration': d.concentration or self.concentration,
					'basic_rate': self.per_unit_amount,
					'valuation_rate': self.per_unit_amount,
					'basic_amount': flt(d.qty * self.per_unit_amount),
					'cost_center': cost_center
				})
			se.save()
			se.submit()
			self.db_set('stock_entry',se.name)
			batch = None
			for row in self.packaging:
				batch_name = frappe.db.sql("""
					SELECT sed.batch_no from `tabStock Entry` se LEFT JOIN `tabStock Entry Detail` sed on (se.name = sed.parent)
					WHERE 
						se.name = '{name}'
						and (sed.t_warehouse != '' or sed.t_warehouse IS NOT NULL) 
						and sed.qty = {qty}
						and sed.packaging_material = '{packaging_material}'
						and sed.packing_size = '{packing_size}'
						and sed.no_of_packages = {no_of_packages}""".format(
							name=se.name,
							qty=row.qty,
							packaging_material=row.packaging_material,
							packing_size=row.packing_size,
							no_of_packages=row.no_of_packages,
						))
				if batch_name:
					batch = batch_name[0][0] or ''

				if batch:
					row.db_set('batch_no', batch)
					if self.customer_name:
						frappe.db.set_value("Batch",batch,'customer',self.customer_name)
					if self.lot_no:
						frappe.db.set_value("Batch",batch,'sample_ref_no',self.lot_no)
		
	def before_cancel(self):
		for item in self.packaging:
			item.db_set('lot_no', None)
			item.db_set('batch_no', None)
		
	def on_cancel(self):
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry",self.stock_entry)
			se.cancel()
			self.db_set('stock_entry','')

			for row in self.packaging:
				row.db_set('batch_no', '')

	def cal_total(self):
		self.amount = sum([flt(row.basic_amount) for row in self.items])
		self.per_unit_amount = self.amount/ self.actual_qty
		self.total_qty = sum([flt(item.qty) for item in self.items])		
		self.total_quantity = sum([flt(item.quantity) for item in self.items])
		self.actual_quantity = sum([flt(item.quantity) for item in self.packaging])
		self.total_packing_qty = sum([flt(item.qty) for item in self.packaging])
		self.total_packing_quantity = sum([flt(item.quantity) for item in self.packaging])
		if self.actual_quantity:
			self.price = flt(self.amount)/ flt(self.actual_quantity)

	def before_save(self):
		self.handling_loss = flt(self.total_qty) - flt(self.actual_qty)
	
	def validate_qty(self):
		total_qty = sum([flt(row.qty) for row in self.packaging])
		if self.actual_qty != total_qty:
			frappe.throw("Sum of Qty should be match with actual qty")

from erpnext.utilities.product import get_price
@frappe.whitelist()
def get_price_list(item_code, price_list, customer_group="All Customer Groups", company=None):
	price = get_price(item_code, price_list, customer_group, company)
	
	if not price:
		price = frappe._dict({'price_list_rate': 0.0})

	return price

@frappe.whitelist()
def make_outward_sample(source_name, target_doc=None):
	def postprocess(source, doc):

		doc.link_to = "Customer"
		customer_name, destination = frappe.db.get_value("Customer", doc.party, ['customer_name', 'territory'])
		doc.party_name = customer_name
		doc.destination_1 = doc.destination = destination

		total_amount = 0.0
		for d in doc.details:
			price = get_price_list(d.item_name, "Standard Buying").price_list_rate

			if d.batch_yield:
				bomyield = frappe.db.get_value("BOM",{'item': d.item_name},"batch_yield")
				if bomyield != 0:
					d.rate = (price * flt(bomyield)) / d.batch_yield
				else:
					d.rate = (price * 2.2) / d.batch_yield
			else:
				d.rate = price
			 
			d.price_list_rate = price
			d.amount = flt(d.rate) * d.quantity
			total_amount += d.amount

		doc.total_amount = flt(total_amount)
		doc.total_qty = source.actual_qty
		doc.per_unit_price = flt(total_amount) / flt(doc.total_qty)

	doc = get_mapped_doc("Ball Mill Data Sheet", source_name, {
		"Ball Mill Data Sheet": {
			"doctype": "Outward Sample",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map": {
				"name": 'ball_mill_ref',
				"customer_name": "party",
				"total_yield": "batch_yield"
			},
			"field_no_map": [
				"naming_series",
				"remarks"
			]
		},
		"Ball Mill Data Sheet Item": {
			"doctype": "Outward Sample Detail",
		}
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def get_sales_order(doctype, txt, searchfield, start, page_len, filters):
	meta = frappe.get_meta("Sales Order")
	searchfield = meta.get_search_fields()

	sales_order_list = frappe.db.sql("""
			SELECT so.name from `tabSales Order` as so 
			LEFT JOIN `tabSales Order Item` as soi 
			ON so.name = soi.parent
			WHERE so.docstatus = '1' and so.customer  = '{0}' and soi.item_code = '{1}' and status NOT IN ('Closed','Completed')""" 
			.format(filters.get("customer_name"),filters.get("product_name")))

	return sales_order_list

@frappe.whitelist()
def get_sample_no(parent,item_code):
	value = frappe.db.get_value("Sales Order Item", {'parent': parent,'item_code': item_code}, 'outward_sample')
	return value
	
	