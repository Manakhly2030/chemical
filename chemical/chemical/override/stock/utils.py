from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
import json
from frappe.utils import flt, cstr, nowdate, nowtime, cint

@frappe.whitelist()
def get_incoming_rate(args, raise_error_if_no_rate=True):
	"""Get Incoming Rate based on valuation method"""
	from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
	if isinstance(args, string_types):
		args = json.loads(args)

	in_rate = 0
	#finbyz changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))

	#finbyz changes
	if args.get("batch_no") and batch_wise_cost:
		in_rate = get_batch_rate(args.get("batch_no"))

	if (args.get("serial_no") or "").strip():
		in_rate = get_avg_purchase_rate(args.get("serial_no"))
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

	return in_rate

# finbyz changes
def get_batch_rate(batch_no):
	"""Get Batch Valuation Rate of Batch No"""

	return flt(frappe.db.sql("""SELECT valuation_rate FROM `tabBatch` 
		WHERE name = %s """, batch_no)[0][0])
