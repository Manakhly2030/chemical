# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate

def execute(filters=None):
	if not filters: filters = {}

	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	columns = get_columns(filters)
	item_map = get_item_details(filters)
	iwb_map = get_item_warehouse_batch_map(filters, float_precision)

	data = []
	for item in sorted(iwb_map):
		for wh in sorted(iwb_map[item]):
			for batch in sorted(iwb_map[item][wh]):
				qty_dict = iwb_map[item][wh][batch]
				if qty_dict.opening_qty or qty_dict.in_qty or qty_dict.out_qty or qty_dict.bal_qty:
					lot_no, packaging_material, packing_size, concentration, valuation_rate = frappe.db.get_value("Batch", batch, ["lot_no", "packaging_material","packing_size","concentration","valuation_rate"])
					# data.append([item, wh, batch, lot_no, concentration, packaging_material, packing_size
					# 	flt(qty_dict.bal_qty, float_precision),
					# 	 item_map[item]["stock_uom"]
					# ])
					data.append({
						'item_code': item,
						'item_group': item_map[item]["item_group"],
						'warehouse': wh,
						'batch_no': batch,
						'lot_no': lot_no,
						'concentration': concentration,
						'packaging_material': packaging_material,
						'packing_size': packing_size,
						'bal_qty': flt(qty_dict.bal_qty, float_precision),
						'as_is_qty': flt((qty_dict.bal_qty*100)/concentration, float_precision),
						'valuation_rate':valuation_rate,
						'uom': item_map[item]["stock_uom"]
					})

	return columns, data

def get_columns(filters):
	"""return columns based on filters"""
	columns = [
		{
			"label": _("Item Code"),
			"fieldname": "item_code",
			"fieldtype": "Link",
			"options": "Item",
			"width": 180
		},
		{
			"label": _("Item Group"),
			"fieldname": "item_group",
			"fieldtype": "Link",
			"options": "Item Group",
			"width": 100
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 120
		},
		{
			"label": _("Batch"),
			"fieldname": "batch_no",
			"fieldtype": "Link",
			"options": "Batch",
			"width": 120
		},
		{
			"label": _("Lot No"),
			"fieldname": "lot_no",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Concentration"),
			"fieldname": "concentration",
			"fieldtype": "Float",
			"width": 80
		},
		{
			"label": _("Packaging Material"),
			"fieldname": "packaging_material",
			"fieldtype": "Link",
			"options": "Packaging Material",
			"width": 70
		},
		{
			"label": _("Packing Size"),
			"fieldname": "packing_size",
			"fieldtype": "int",
			"width": 70
		},
		{
			"label": _("Balance Qty"),
			"fieldname": "bal_qty",
			"fieldtype": "Float",
			"width": 90
		},
		{
			"label": _("As is Qty"),
			"fieldname": "as_is_qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Valuation Rate"),
			"fieldname": "valuation_rate",
			"fieldtype": "Currency",
			"width": 80
		},
		{
			"label": _("UOM"),
			"fieldname": "uom",
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80
		},
	]

	return columns

def get_conditions(filters):
	conditions = ""
	if filters.get("to_date"):
		conditions += " and posting_date <= '%s'" % filters["to_date"]
	else:
		frappe.throw(_("'To Date' is required"))

	if filters.get("warehouse"):
		conditions += " and warehouse = '%s'" % filters["warehouse"]

	if filters.get("item_code"):
		conditions += " and item_code = '%s'" % filters["item_code"]

	return conditions

#get all details
def get_stock_ledger_entries(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""
		select item_code, batch_no, warehouse, posting_date, sum(actual_qty) as actual_qty
		from `tabStock Ledger Entry`
		where docstatus < 2 and ifnull(batch_no, '') != '' %s
		group by voucher_no, batch_no, item_code, warehouse
		order by item_code, warehouse""" %
		conditions, as_dict=1)

def get_item_warehouse_batch_map(filters, float_precision):
	sle = get_stock_ledger_entries(filters)
	iwb_map = {}

	from_date = getdate(filters["to_date"])
	to_date = getdate(filters["to_date"])

	for d in sle:
		iwb_map.setdefault(d.item_code, {}).setdefault(d.warehouse, {})\
			.setdefault(d.batch_no, frappe._dict({
				"opening_qty": 0.0, "in_qty": 0.0, "out_qty": 0.0, "bal_qty": 0.0
			}))
		qty_dict = iwb_map[d.item_code][d.warehouse][d.batch_no]
		if d.posting_date < from_date:
			qty_dict.opening_qty = flt(qty_dict.opening_qty, float_precision) \
				+ flt(d.actual_qty, float_precision)
		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(d.actual_qty) > 0:
				qty_dict.in_qty = flt(qty_dict.in_qty, float_precision) + flt(d.actual_qty, float_precision)
			else:
				qty_dict.out_qty = flt(qty_dict.out_qty, float_precision) \
					+ abs(flt(d.actual_qty, float_precision))

		qty_dict.bal_qty = flt(qty_dict.bal_qty, float_precision) + flt(d.actual_qty, float_precision)

	return iwb_map

def get_item_details(filters):
	item_map = {}
	for d in frappe.db.sql("select name, item_name, description, stock_uom, item_group from tabItem", as_dict=1):
		item_map.setdefault(d.name, d)

	return item_map
