# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
# import frappe
import re

# function to clean string for names in coloumn
def clean_string(string):
	if string:
		string = string.replace(" ", "_")
		string = string.lower()
		string = re.sub('[^A-Za-z0-9_]+', '', string)
	return string

def execute(filters=None):
	if not filters: filters = {}
	from_date = filters.get("from_date", None)
	to_date = filters.get("to_date", None)

	if from_date and to_date:
		if from_date > to_date:
			frappe.throw(_("From Date cannot be less than To Date"))

	columns = get_columns(filters)
	data = get_data(filters)
	
	return columns, data

def get_columns(filters):
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "options": "Work Order", "width": 150},
		{"label": _("Date"), "fieldname": "planned_start_date", "fieldtype": "Date", "width": 150},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 120},
		# {"label": _("Qty To Manufacture"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": _("As is Qty"), "fieldname": "produced_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Manufactured Qty"), "fieldname": "real_produced_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Yield"), "fieldname": "batch_yield", "fieldtype": "Percent", "width": 80},
	]

	# append dynamic columns for item used for Manufacturing
	data = column_query(filters)
	if data:
		columns.append({"label": _("{}".format(data[0][1])), "fieldname": str(clean_string(data[0][1])), "fieldtype": "Float", "width": 100})
	for d in data:
		if d[0] != d[1]:
			x = {"label": _("{}".format(d[0])), "fieldname": str(clean_string(d[0])), "fieldtype": "Float", "width": 100}
			columns.append(x)

	# columns += [
	# 	# {"label": _("Concentration / Purity"), "fieldname": "concentration", "fieldtype": "Percent", "width": 100},
	# 	# {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 80},
	# ]

	return columns

def get_data(filters):
	data = data_query(filters)

	return data

def column_query(filters):
	# get production item from filters
	production_item = re.escape(filters.get("production_item", ""))
	conditions = ''
	if filters.get("from_date"):		
		conditions += "AND DATE(wo.planned_start_date) >= '{}' \n".format(str(filters.get("from_date")))
		
	if filters.get("to_date"):
		conditions += "AND DATE(wo.planned_start_date) <= '{}' \n".format(str(filters.get("to_date")))

	if re.escape(filters.get("company","")):
		conditions += "AND wo.company = '{}' \n".format(re.escape(filters.get("company","")))

	# Getting dynamic column name
	column = frappe.db.sql("""SELECT item_code,based_on from `tabWork Order Item` as woi
	LEFT JOIN `tabWork Order` as wo ON woi.parent = wo.name 
	WHERE `production_item` = '{}' {}
	GROUP BY item_code
	ORDER BY woi.idx
	""".format(production_item,conditions)
	)

	return column

def data_query(filters):
	# getting data from filters
	production_item = re.escape(filters.get("production_item", ""))
	company = re.escape(filters.get("company", ""))
	from_date = filters.get("from_date", None)
	to_date = filters.get("to_date", None)
	
	# adding where condition according to filters
	condition = ''
	format_ = '%Y-%m-%d %H:%M:%S'
	if from_date:		
		condition += 'AND ' if condition != '' else 'WHERE '
		condition += "DATE(wo.planned_start_date) >= '{}' \n".format(str(from_date))
		
	if to_date:
		condition += 'AND ' if condition != '' else 'WHERE '
		condition += "DATE(wo.planned_start_date) <= '{}' \n".format(str(to_date))

	if production_item:
		condition += 'AND ' if condition != '' else 'WHERE '
		condition += "wo.production_item = '{}' \n".format(production_item)
	
	if company:
		condition += 'AND ' if condition != '' else 'WHERE '
		condition += "wo.company = '{}' \n".format(company)
	
	# sql query to get data for column
	data = frappe.db.sql("""SELECT 
	wo.planned_start_date, 
	wo.name,
	wo.qty,
	wo.lot_no,
	wo.produced_qty,
	wo.produced_quantity,
	wo.concentration,
	wo.valuation_rate,
	wo.batch_yield
	FROM  `tabWork Order Item` as woi
	LEFT JOIN `tabWork Order` as wo ON woi.parent = wo.name 
	{}
	GROUP BY wo.name
	""".format(condition), as_dict=1)

	# sub query to find transferred quantity of item used for manufacturing
	for item in data:
		name = item.get('name', '')
		produced_qty = item.get('produced_qty', 0)
		concentration = item.get('concentration', 0)

		# frappe.msgprint(name)
		sub_data = frappe.db.sql("""SELECT 
		item_code,transferred_qty 
		FROM `tabWork Order Item` 
		WHERE parent = '{}'""".format(name))

		for key, value in sub_data:
			key = clean_string(key)
			item[key] = value
		
		# calculating real manufacturing quantity
		item['real_produced_qty'] = produced_qty * (concentration / 100)
	
	return data

