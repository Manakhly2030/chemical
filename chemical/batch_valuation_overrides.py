import frappe, erpnext
from frappe import msgprint, _
from frappe.utils import nowdate, flt, cint, cstr,now_datetime,nowtime
from erpnext.stock.stock_ledger import update_entries_after,get_valuation_rate
from erpnext.controllers.sales_and_purchase_return import get_return_against_item_fields,get_filters
from erpnext.stock.utils import get_valuation_method,get_fifo_rate
from six import string_types

import json

# Utils Overrides
@frappe.whitelist()
def get_incoming_rate(args, raise_error_if_no_rate=True):
	"""Get Incoming Rate based on valuation method"""
	from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
	if isinstance(args, string_types):
		args = json.loads(args)

	in_rate = 0

	#finbyz changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))
	
	if (args.get("serial_no") or "").strip():
		in_rate = get_avg_purchase_rate(args.get("serial_no"))

	#finbyz 
	elif args.get("batch_no") and batch_wise_cost:
		in_rate = get_batch_rate(args)

	else:
		valuation_method = get_valuation_method(args.get("item_code"))
		previous_sle = get_previous_sle(args)
		if valuation_method == 'FIFO':
			if previous_sle:
				previous_stock_queue = json.loads(previous_sle.get('stock_queue', '[]') or '[]')
				in_rate = get_fifo_rate(previous_stock_queue, args.get("qty") or 0) if previous_stock_queue else 0
		elif valuation_method == 'Moving Average':
			in_rate = previous_sle.get('valuation_rate') or 0

	if not in_rate:
		voucher_no = args.get('voucher_no') or args.get('name')
		in_rate = get_valuation_rate(args.get('item_code'), args.get('warehouse'),
			args.get('voucher_type'), voucher_no, args.get('allow_zero_valuation'),
			currency=erpnext.get_company_currency(args.get('company')), company=args.get('company'),
			raise_error_if_no_rate=raise_error_if_no_rate)

	return flt(in_rate)

#FinByz changes
def get_batch_rate(args):
	"""Get Batch Valuation Rate of Batch No"""
	
	item_code = args.get('item_code')
	batch_no = args.get('batch_no')

	conditions = "and item_code = '{item_code}' and batch_no = '{batch_no}' ".format(item_code=item_code,batch_no=batch_no)
	
	if args.get("warehouse"):
		warehouse = args.get("warehouse")
		conditions += " and warehouse = '{warehouse}' ".format(warehouse=warehouse)

	if args.get("company"):
		company =  args.get("company")
		conditions += " and company = '{company}' ".format(company=company)

	data = frappe.db.sql("""SELECT incoming_rate FROM `tabStock Ledger Entry` 
		WHERE actual_qty > 0 and docstatus = 1 and is_cancelled = 0 {conditions} order by posting_date desc, posting_time desc, creation desc""".format(conditions=conditions))
	
	if data:
		data = flt(data[0][0])

	return flt(data)

# Stock Ledger Overides
def process_sle(self, sle):
	# previous sle data for this warehouse
	self.wh_data = self.data[sle.warehouse]

	if (sle.serial_no and not self.via_landed_cost_voucher) or not cint(self.allow_negative_stock):
		# validate negative stock for serialized items, fifo valuation
		# or when negative stock is not allowed for moving average
		if not self.validate_negative_stock(sle):
			self.wh_data.qty_after_transaction += flt(sle.actual_qty)
			return

	# Get dynamic incoming/outgoing rate
	self.get_dynamic_incoming_outgoing_rate(sle)

	# Finbyz Changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))
	if sle.batch_no and batch_wise_cost:
		get_batch_values(self,sle)
		self.wh_data.qty_after_transaction += flt(sle.actual_qty)
		# if sle.voucher_type == "Stock Reconciliation":
		# 	self.wh_data.qty_after_transaction = sle.qty_after_transaction
		self.wh_data.stock_value = flt(self.wh_data.qty_after_transaction) * flt(self.wh_data.valuation_rate)

	elif sle.serial_no:
		self.get_serialized_values(sle)
		self.wh_data.qty_after_transaction += flt(sle.actual_qty)
		if sle.voucher_type == "Stock Reconciliation":
			self.wh_data.qty_after_transaction = sle.qty_after_transaction

		self.wh_data.stock_value = flt(self.wh_data.qty_after_transaction) * flt(self.wh_data.valuation_rate)
		
	else:
		if sle.voucher_type=="Stock Reconciliation" and not sle.batch_no:
			# assert
			self.wh_data.valuation_rate = sle.valuation_rate
			self.wh_data.qty_after_transaction = sle.qty_after_transaction
			self.wh_data.stock_queue = [[self.wh_data.qty_after_transaction, self.wh_data.valuation_rate]]
			self.wh_data.stock_value = flt(self.wh_data.qty_after_transaction) * flt(self.wh_data.valuation_rate)
		else:
			if self.valuation_method == "Moving Average":
				self.get_moving_average_values(sle)
				self.wh_data.qty_after_transaction += flt(sle.actual_qty)
				self.wh_data.stock_value = flt(self.wh_data.qty_after_transaction) * flt(self.wh_data.valuation_rate)
			else:
				self.get_fifo_values(sle)
				self.wh_data.qty_after_transaction += flt(sle.actual_qty)
				self.wh_data.stock_value = sum((flt(batch[0]) * flt(batch[1]) for batch in self.wh_data.stock_queue))

	# rounding as per precision
	self.wh_data.stock_value = flt(self.wh_data.stock_value, self.precision)
	stock_value_difference = self.wh_data.stock_value - self.wh_data.prev_stock_value
	self.wh_data.prev_stock_value = self.wh_data.stock_value

	# update current sle
	sle.qty_after_transaction = self.wh_data.qty_after_transaction
	sle.valuation_rate = self.wh_data.valuation_rate
	sle.stock_value = self.wh_data.stock_value
	sle.stock_queue = json.dumps(self.wh_data.stock_queue)
	sle.stock_value_difference = stock_value_difference
	sle.doctype="Stock Ledger Entry"
	frappe.get_doc(sle).db_update()

	self.update_outgoing_rate_on_transaction(sle)

# Finbyz changes
def get_batch_values(self, sle):
	
	incoming_rate = flt(sle.incoming_rate)
	actual_qty = flt(sle.actual_qty)
	batch_no = cstr(sle.batch_no)
	item_code = cstr(sle.item_code)
	conditions = "and item_code = '{item_code}' and batch_no = '{batch_no}' ".format(item_code=item_code,batch_no=batch_no)

	if sle.get("warehouse"):
		warehouse = sle.get("warehouse")
		conditions += " and warehouse = '{warehouse}' ".format(warehouse=warehouse)

	if sle.get("company"):
		company =  sle.get("company")
		conditions += " and company = '{company}' ".format(company=company)

	if incoming_rate < 0:
		# wrong incoming rate
		incoming_rate = self.wh_data.valuation_rate

	stock_value_change = 0
	if incoming_rate:
		stock_value_change = actual_qty * incoming_rate
		
	elif actual_qty < 0:
		# In case of delivery/stock issue, get average purchase rate
		# of serial nos of current entry
		stock_value_change = actual_qty * flt(frappe.db.sql("""SELECT incoming_rate FROM `tabStock Ledger Entry` 
	WHERE actual_qty > 0 and docstatus = 1 and is_cancelled = 0 {conditions} order by posting_date desc, posting_time desc, creation desc""".format(conditions=conditions))[0][0])

	new_stock_qty = self.wh_data.qty_after_transaction + actual_qty
	if new_stock_qty > 0:
		new_stock_value = (self.wh_data.qty_after_transaction * self.wh_data.valuation_rate) + stock_value_change
		if new_stock_value >= 0:
			# calculate new valuation rate only if stock value is positive
			# else it remains the same as that of previous entry
			self.wh_data.valuation_rate = new_stock_value / new_stock_qty

	if not self.wh_data.valuation_rate and sle.voucher_detail_no:
		allow_zero_rate = self.check_if_allow_zero_valuation_rate(sle.voucher_type, sle.voucher_detail_no)
		if not allow_zero_rate:
			self.wh_data.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
				sle.voucher_type, sle.voucher_no, self.allow_zero_rate,
				currency=erpnext.get_company_currency(sle.company))

# Stock Entry Overrides

def get_args_for_incoming_rate(self, item):
	return frappe._dict({
		"item_code": item.item_code,
		"warehouse": item.s_warehouse or item.t_warehouse,
		"posting_date": self.posting_date,
		"posting_time": self.posting_time,
		"qty": item.s_warehouse and -1*flt(item.transfer_qty) or flt(item.transfer_qty),
		"serial_no": item.serial_no,
		"voucher_type": self.doctype,
		"voucher_no": self.name,
		"company": self.company,
		"allow_zero_valuation": item.allow_zero_valuation_rate,
		"batch_no": item.batch_no, # FinByz Changes
	})

# Buying Controller overrides
def get_supplied_items_cost(self, item_row_id, reset_outgoing_rate=True):
	supplied_items_cost = 0.0
	for d in self.get("supplied_items"):
		if d.reference_name == item_row_id:
			if reset_outgoing_rate and frappe.db.get_value('Item', d.rm_item_code, 'is_stock_item'):
				rate = get_incoming_rate({
					"item_code": d.rm_item_code,
					"warehouse": self.supplier_warehouse,
					"posting_date": self.posting_date,
					"posting_time": self.posting_time,
					"qty": -1 * d.consumed_qty,
					"serial_no": d.serial_no,
					"batch_no": d.batch_no #FinByz Changes
				})

				if rate > 0:
					d.rate = rate

			d.amount = flt(flt(d.consumed_qty) * flt(d.rate), d.precision("amount"))
			supplied_items_cost += flt(d.amount)

	return supplied_items_cost

def set_incoming_rate_buying(self):
	if self.doctype not in ("Purchase Receipt", "Purchase Invoice", "Purchase Order"):
		return

	ref_doctype_map = {
		"Purchase Order": "Sales Order Item",
		"Purchase Receipt": "Delivery Note Item",
		"Purchase Invoice": "Sales Invoice Item",
	}

	ref_doctype = ref_doctype_map.get(self.doctype)
	items = self.get("items")
	for d in items:
		if not cint(self.get("is_return")):
			# Get outgoing rate based on original item cost based on valuation method

			if not d.get(frappe.scrub(ref_doctype)):
				outgoing_rate = get_incoming_rate({
					"item_code": d.item_code,
					"warehouse": d.get('from_warehouse'),
					"posting_date": self.get('posting_date') or self.get('transation_date'),
					"posting_time": self.get('posting_time'),
					"qty": -1 * flt(d.get('stock_qty')),
					"serial_no": d.get('serial_no'),
					"company": self.company,
					"voucher_type": self.doctype,
					"voucher_no": self.name,
					"allow_zero_valuation": d.get("allow_zero_valuation"),
					"batch_no": d.get('batch_no') #FinByz Changes"
				}, raise_error_if_no_rate=False)

				rate = flt(outgoing_rate * d.conversion_factor, d.precision('rate'))
			else:
				rate = frappe.db.get_value(ref_doctype, d.get(frappe.scrub(ref_doctype)), 'rate')

			if self.is_internal_transfer():
				if rate != d.rate:
					d.rate = rate
					d.discount_percentage = 0
					d.discount_amount = 0
					frappe.msgprint(_("Row {0}: Item rate has been updated as per valuation rate since its an internal stock transfer")
						.format(d.idx), alert=1)

# Selling Controller Overrides
def set_incoming_rate_selling(self):
	if self.doctype not in ("Delivery Note", "Sales Invoice", "Sales Order"):
		return

	items = self.get("items") + (self.get("packed_items") or [])
	for d in items:
		if not self.get("return_against"):
			# Get incoming rate based on original item cost based on valuation method
			qty = flt(d.get('stock_qty') or d.get('actual_qty'))

			d.incoming_rate = get_incoming_rate({
				"item_code": d.item_code,
				"warehouse": d.warehouse,
				"posting_date": self.get('posting_date') or self.get('transaction_date'),
				"posting_time": self.get('posting_time') or nowtime(),
				"qty": qty if cint(self.get("is_return")) else (-1 * qty),
				"serial_no": d.get('serial_no'),
				"company": self.company,
				"voucher_type": self.doctype,
				"voucher_no": self.name,
				"allow_zero_valuation": d.get("allow_zero_valuation"),
				"batch_no": d.get('batch_no') #FinByz Changes
			}, raise_error_if_no_rate=False)

			# For internal transfers use incoming rate as the valuation rate
			if self.is_internal_transfer():
				rate = flt(d.incoming_rate * d.conversion_factor, d.precision('rate'))
				if d.rate != rate:
					d.rate = rate
					d.discount_percentage = 0
					d.discount_amount = 0
					frappe.msgprint(_("Row {0}: Item rate has been updated as per valuation rate since its an internal stock transfer")
						.format(d.idx), alert=1)

		elif self.get("return_against"):
			# Get incoming rate of return entry from reference document
			# based on original item cost as per valuation method
			d.incoming_rate = get_rate_for_return(self.doctype, self.name, d.item_code, self.return_against, item_row=d)


# sales and purchase return
def get_rate_for_return(voucher_type, voucher_no, item_code, return_against=None,
	item_row=None, voucher_detail_no=None, sle=None):
	if not return_against:
		return_against = frappe.get_cached_value(voucher_type, voucher_no, "return_against")

	if not return_against and voucher_type == 'Sales Invoice' and sle:
		return get_incoming_rate({
			"item_code": sle.item_code,
			"warehouse": sle.warehouse,
			"posting_date": sle.get('posting_date'),
			"posting_time": sle.get('posting_time'),
			"qty": sle.actual_qty,
			"serial_no": sle.get('serial_no'),
			"company": sle.company,
			"voucher_type": sle.voucher_type,
			"voucher_no": sle.voucher_no,
			"batch_no":sle.batch_no # Finbyz Changes
		}, raise_error_if_no_rate=False)

	return_against_item_field = get_return_against_item_fields(voucher_type)

	filters = get_filters(voucher_type, voucher_no, voucher_detail_no,
		return_against, item_code, return_against_item_field, item_row)

	if voucher_type in ("Purchase Receipt", "Purchase Invoice"):
		select_field = "incoming_rate"
	else:
		select_field = "abs(stock_value_difference / actual_qty)"

	return flt(frappe.db.get_value("Stock Ledger Entry", filters, select_field))
