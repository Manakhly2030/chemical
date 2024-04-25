# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe,datetime
from frappe import _
from frappe.utils import flt, cint, cstr
from frappe.desk.reportview import get_match_cond
from erpnext.stock.stock_ledger import get_valuation_rate

def batch_wise_cost():
	return cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))

@frappe.whitelist()
def pr_validate(self, method):
	if batch_wise_cost() and not self.is_return:
		make_batches(self, 'warehouse')

@frappe.whitelist()
def pr_on_cancel(self, method):
	if not self.is_return:
		delete_batches(self, 'warehouse')

@frappe.whitelist()
def pi_validate(self, method):
	if self.update_stock and batch_wise_cost() and not self.is_return:
		make_batches(self, 'warehouse')

@frappe.whitelist()
def pi_on_cancel(self, method):
	if self.update_stock and not self.is_return:
		delete_batches(self, 'warehouse')

@frappe.whitelist()
def stock_entry_validate(self, method):
	if batch_wise_cost():
		if self.purpose not in ['Material Transfer', 'Material Transfer for Manufacture']:
			make_batches(self, 't_warehouse')
			
			
	if self.purpose in ['Repack','Manufacture','Material Issue']:
		self.get_stock_and_rate()
	if self._action == "submit":
		validate_additional_cost(self,method)

def validate_additional_cost(self,method):
	if self.purpose in ['Repack','Manufacture'] and self._action == "submit":
		# frappe.throw(str(self.value_difference))
		# frappe.throw(str(self.total_additional_costs))
		diff = abs(round(flt(self.value_difference,1)) - (round(flt(self.total_additional_costs,1))))
		if diff > 5:
			frappe.throw(f"ValuationError: Value difference {diff} between incoming and outgoing amount is higher than additional cost")

@frappe.whitelist()
def stock_entry_on_submit(self, method):
	if batch_wise_cost():
		if self.purpose in ['Material Transfer', 'Material Transfer for Manufacture']:
			make_transfer_batches(self)
			update_stock_ledger_batch(self)

def make_transfer_batches(self):
	validate_concentration(self, 't_warehouse')

	for row in self.items:
		if not row.get('t_warehouse'):
			continue

		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
		if has_batch_no:
			if row.batch_no:
				if not frappe.db.get_value("Stock Ledger Entry", {'is_cancelled':0,'company':self.company,'warehouse':row.get('t_warehouse'),'batch_no':row.batch_no,'incoming_rate':('!=', 0),'voucher_no':('!=',self.name)},"incoming_rate"):
					continue
				elif row.valuation_rate == frappe.db.get_value("Stock Ledger Entry", {'is_cancelled':0,'company':self.company,'warehouse':row.get('t_warehouse'),'batch_no':row.batch_no,'incoming_rate':('!=', 0),'voucher_no':('!=',self.name)},"incoming_rate"):
					if hasattr(self, 'send_to_party') and hasattr(row, 'party_concentration'):
						if not self.send_to_party:
							continue
						if row.party_concentration == row.concentration:
							continue
					else:
						continue	
				else:
					row.db_set('old_batch_no', row.batch_no)

			batch = frappe.new_doc("Batch")
			batch.item = row.item_code
			batch.lot_no = cstr(row.lot_no)
			batch.packaging_material = cstr(row.packaging_material)
			batch.packing_size = cstr(row.packing_size)
			batch.batch_yield = flt(row.batch_yield, 3)
			if hasattr(self, 'send_to_party') and hasattr(row, 'party_concentration'):
				if self.send_to_party and row.party_concentration != row.concentration:
					batch.concentration = flt(row.party_concentration, 3) or flt(row.concentration, 3)
				else:
					batch.concentration = flt(row.concentration, 3)	
			else:
				batch.concentration = flt(row.concentration, 3)
			batch.valuation_rate = flt(row.valuation_rate, 4)
			try:
				batch.posting_date = datetime.datetime.strptime(self.posting_date, "%Y-%m-%d").strftime("%y%m%d")
			except:
				batch.posting_date = self.posting_date.strftime("%y%m%d")
			batch.actual_quantity = flt(row.qty * row.conversion_factor)
			batch.reference_doctype = self.doctype
			batch.reference_name = self.name
			batch.insert()
			row.db_set('batch_no', batch.name)


@frappe.whitelist()
def stock_entry_on_cancel(self, method):
	if self.purpose in ['Material Transfer', 'Material Transfer for Manufacture']:
		delete_transfer_batches(self)
	else:
		delete_batches(self, 't_warehouse')

def delete_transfer_batches(self):
	from frappe.model.delete_doc import check_if_doc_is_linked
	
	for row in self.items:
		if row.batch_no and row.get('t_warehouse'):
			batch_no = frappe.get_doc("Batch", row.batch_no)
			if batch_no.valuation_rate == row.valuation_rate and not row.get('old_batch_no'):
				continue

			row.batch_no = row.old_batch_no
			if batch_no.reference_name == self.name:
				frappe.db.set_value("Batch",batch_no.name,'reference_name',' ')
			#check_if_doc_is_linked(batch_no)
			#frappe.delete_doc("Batch", batch_no.name)
			row.db_set('batch_no', row.old_batch_no)
			row.db_set('old_batch_no', '')
	# else:
	# 	frappe.db.commit()

def update_stock_ledger_batch(self):
	for row in self.get('items'):
		sle = frappe.get_doc("Stock Ledger Entry", {
			'voucher_no': self.name,
			'voucher_detail_no': row.name,
			'warehouse': row.t_warehouse,
			'is_cancelled':0,
		})

		if sle:
			sle.db_set('batch_no', row.batch_no)

def set_basic_rate_for_t_warehouse(self):
	s_warehouse_rates = [d.valuation_rate * d.qty for d in self.get('items') if d.s_warehouse and not d.t_warehouse]

	for d in self.get('items'):
		if d.t_warehouse:
			d.basic_rate = (sum(s_warehouse_rates) / flt(d.qty))

	self.run_method('calculate_rate_and_amount')

def make_batches(self, warehouse_field):
	# import datetime
	
	if self._action == "submit":
		validate_concentration(self, warehouse_field)

		for row in self.items:
			if self.doctype == 'Stock Entry' and self.purpose in ['Material Transfer', 'Material Transfer for Manufacture']:
				continue
			if not row.get(warehouse_field):
				continue
			
			has_batch_no, create_new_batch = frappe.db.get_value(
								"Item", row.item_code, ["has_batch_no", "create_new_batch"]
							)
			
			has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
			if has_batch_no and create_new_batch and not row.batch_no:
				if row.batch_no and flt(row.valuation_rate,4) == flt(frappe.db.get_value("Stock Ledger Entry", {'is_cancelled':0,'company':self.company,'warehouse':row.get(warehouse_field),'batch_no':row.batch_no,'incoming_rate':('!=', 0)},'incoming_rate'),4):
				# if row.batch_no and not frappe.db.exists("Stock Ledger Entry", {'is_cancelled':0,'company':self.company,'warehouse':row.get(warehouse_field),'batch_no':row.batch_no}):
					continue

				if row.batch_no and self.doctype == "Stock Entry":
					row.db_set('old_batch_no', row.batch_no)

						
				# frappe.throw('test')
				batch = frappe.new_doc("Batch")
				batch.item = row.item_code
				batch.supplier = getattr(self, 'supplier', None)
				batch.lot_no = cstr(row.lot_no)
				batch.packaging_material = cstr(row.packaging_material)
				batch.packing_size = cstr(row.packing_size)
				batch.batch_yield = flt(row.batch_yield, 3)
				batch.concentration = flt(row.concentration, 3)
				batch.valuation_rate = flt(row.valuation_rate, 4)
				# batch.price = flt(row.price,2)

				if self.doctype == "Stock Entry":
					if self.stock_entry_type == "Manufacture" or self.stock_entry_type == "Material Receipt" :
						batch.manufacturing_date = self.posting_date
				try:
					batch.posting_date = datetime.datetime.strptime(self.posting_date, "%Y-%m-%d").strftime("%y%m%d")
				except:
					batch.posting_date = self.posting_date.strftime("%y%m%d")
				batch.actual_quantity = flt(row.qty * row.conversion_factor)
				batch.reference_doctype = self.doctype
				batch.reference_name = self.name
				batch.insert()
				row.batch_no = batch.name



def delete_batches(self, warehouse):
	from frappe.model.delete_doc import check_if_doc_is_linked
	
	for row in self.items:
		if row.batch_no and row.get(warehouse):
			batch_no = frappe.get_doc("Batch", row.batch_no)

			if self.get('work_order') and frappe.db.get_value("Work Order", self.work_order, 'batch'):
				frappe.db.set_value("Work Order", self.work_order, 'batch', '')

			frappe.db.set_value('Batch',row.batch_no,'reference_name',None)
			row.db_set('batch_no', "")
			row.db_set('batch_no', None)
			frappe.db.set_value('Batch',row.batch_no,'disabled',1)
			#row.batch_no = ''
			#check_if_doc_is_linked(batch_no)
			#frappe.delete_doc("Batch", batch_no.name)
	# else:
	# 	frappe.db.commit()

def validate_concentration(self, warehouse_field):
	for row in self.items:
		if not row.get(warehouse_field):
			continue

		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
		if has_batch_no and not flt(row.concentration):
			frappe.throw(_("Row #{idx}. Concentration cannot be 0 for batch wise item - {item_code}.".format(idx = row.idx, item_code = frappe.bold(row.item_code))))

@frappe.whitelist()
def override_batch_autoname(self, method):
	from erpnext.stock.doctype.batch.batch import Batch
	Batch.autoname = batch_autoname

def batch_autoname(self):
	from frappe.model.naming import make_autoname
	
	batch_series, batch_wise_cost = frappe.db.get_value("Stock Settings", None, ['batch_series', 'exact_cost_valuation_for_batch_wise_items'])
	series = 'BTH-.YY.MM.DD.-.###'

	if batch_wise_cost and batch_series:
		series = batch_series

	name = None
	while not name:
		name = make_autoname(series, "Batch", self)
		if frappe.db.exists('Batch', name):
			name = None

	self.batch_id = name
	self.name = name

@frappe.whitelist()
def get_batch_no(doctype, txt, searchfield, start, page_len, filters):
	cond = ""

	meta = frappe.get_meta("Batch")
	searchfield = meta.get_search_fields()

	searchfields = " or ".join(["batch." + field + " like %(txt)s" for field in searchfield])

	if filters.get("posting_date"):
		cond = "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"
		
	# if filters.get("customer"):
	# 	cond = "and (batch.customer = %(customer)s or ifnull(batch.customer, '') = '') "

	batch_nos = None
	args = {
		'item_code': filters.get("item_code"),
		'warehouse': filters.get("warehouse"),
		'posting_date': filters.get('posting_date'),
		'txt': "%{0}%".format(txt),
		"start": start,
		"page_len": page_len
	}

	if args.get('warehouse'):
		batch_nos = frappe.db.sql("""select sle.batch_no, batch.lot_no, round(sum(sle.actual_qty),2), sle.stock_uom, batch.customer
				from `tabStock Ledger Entry` sle
				    INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
				where
					sle.is_cancelled = 0 and
					sle.item_code = %(item_code)s
					and sle.warehouse = %(warehouse)s
					and batch.docstatus < 2
					and (sle.batch_no like %(txt)s or {searchfields})
					{0}
					{match_conditions}
				group by batch_no having sum(sle.actual_qty) > 0
				order by batch.expiry_date, sle.batch_no desc
				limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype), searchfields=searchfields), args)

	if batch_nos:
		return batch_nos
	else:
		return []
	# else:
	# 	return frappe.db.sql("""select name, lot_no, expiry_date from `tabBatch` batch
	# 		where item = %(item_code)s
	# 		and name like %(txt)s
	# 		and docstatus < 2
	# 		{0}
	# 		{match_conditions}
	# 		order by expiry_date, name desc
	# 		limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype)), args)

@frappe.whitelist()
def lcv_validate(self, method):
	if self._action == "submit" and batch_wise_cost():
		validate_batch_actual_qty(self)

@frappe.whitelist()
def lcv_on_submit(self, method):
	if batch_wise_cost():
		update_batch_valuation(self)

@frappe.whitelist()
def lcv_on_cancel(self, method):
	if batch_wise_cost():
		update_batch_valuation(self)

# Update Valuation rate of Purchase Receipt / Purchase Invoice in Batch
def update_batch_valuation(self):
	for d in self.get("purchase_receipts"):
		doc = frappe.get_doc(d.receipt_document_type, d.receipt_document)

		for row in doc.items:
			if row.batch_no:
				batch_doc = frappe.get_doc("Batch", row.batch_no)
				batch_doc.valuation_rate = row.valuation_rate
				batch_doc.save()
		# else:
		# 	frappe.db.commit()

def validate_batch_actual_qty(self):
	from erpnext.stock.doctype.batch.batch import get_batch_qty

	for d in self.get("purchase_receipts"):
		doc = frappe.get_doc(d.receipt_document_type, d.receipt_document)

		for row in doc.items:
			if row.batch_no:
				batch_qty = get_batch_qty(row.batch_no, row.warehouse)

				if batch_qty < row.stock_qty:
					frappe.throw(_("The batch <b>{0}</b> does not have sufficient quantity for item <b>{1}</b> in row {2}.".format(row.batch_no, row.item_code, d.idx)))

@frappe.whitelist()
def get_batch(doctype, txt, searchfield, start, page_len, filters):
	cond = ""

	meta = frappe.get_meta("Batch")
	searchfield = meta.get_search_fields()

	searchfields = " or ".join(["batch." + field + " like %(txt)s" for field in searchfield])

	if filters.get("posting_date"):
		cond = "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"

	batch_nos = None
	args = {
		'item_code': filters.get("item_code"),
		'warehouse': filters.get("warehouse"),
		'posting_date': filters.get('posting_date'),
		'txt': "%{0}%".format(txt),
		"start": start,
		"page_len": page_len
	}

	if args.get('warehouse'):
		return frappe.db.sql("""select sle.batch_no, batch.lot_no, round(sum(sle.actual_qty),2), sle.stock_uom
				from `tabStock Ledger Entry` sle
				    INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
				where
					sle.is_cancelled = 0 and
					sle.item_code = %(item_code)s
					and sle.warehouse = %(warehouse)s
					and batch.docstatus < 2
					and (sle.batch_no like %(txt)s or {searchfields})
					{0}
					{match_conditions}
				group by batch_no having sum(sle.actual_qty) > 0
				order by batch.expiry_date, sle.batch_no desc
				limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype), searchfields=searchfields), args)


def set_incoming_rate(self):
	precision = cint(frappe.db.get_default("float_precision")) 
	for d in self.items:
		if d.s_warehouse:
			args = self.get_args_for_incoming_rate(d)
			d.basic_rate = flt(get_incoming_rate(args), precision)
		elif not d.s_warehouse:
			d.basic_rate = 0.0
		elif self.warehouse and not d.basic_rate:
			d.basic_rate = flt(get_valuation_rate(d.item_code, self.warehouse,
				self.doctype, d.name, 1,
				currency=erpnext.get_company_currency(self.company)), precision)
		d.basic_amount = d.basic_rate * d.qty

import frappe, erpnext
from frappe import _
import json
from frappe.utils import flt, cstr, nowdate, nowtime, cint

def get_incoming_rate(args, raise_error_if_no_rate=True):
	"""Get Incoming Rate based on valuation method"""
	from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
	if isinstance(args, str):
		args = json.loads(args)

	in_rate = 0
	#finbyz changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))

	#finbyz changes
	if args.get("batch_no") :
		in_rate = get_batch_rate(args.get("batch_no"))	
	return in_rate

def get_batch_rate(batch_no):
	"""Get Batch Valuation Rate of Batch No"""

	return flt(frappe.db.sql("""SELECT valuation_rate FROM `tabBatch` 
		WHERE name = %s """, batch_no)[0][0])