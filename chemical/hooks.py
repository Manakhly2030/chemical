# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

# from erpnext.accounts.doctype.opening_invoice_creation_tool.opening_invoice_creation_tool import OpeningInvoiceCreationTool
# from chemical.chemical.doc_events.opening_invoice_creation_tool import get_invoice_dict, make_invoices

# OpeningInvoiceCreationTool.get_invoice_dict = get_invoice_dict
# OpeningInvoiceCreationTool.make_invoices = make_invoices

from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

#Chemical
from chemical.chemical.doc_events.stock_entry import validate_fg_completed_quantity, calculate_rate_and_amount, validate_finished_goods
from chemical.chemical.doc_events.work_order import get_status, update_work_order_qty, update_transaferred_qty_for_required_items, update_consumed_qty_for_required_items

#Chemical
StockEntry.validate_finished_goods = validate_finished_goods
StockEntry.calculate_rate_and_amount = calculate_rate_and_amount
StockEntry.validate_fg_completed_qty = validate_fg_completed_quantity
WorkOrder.get_status = get_status
WorkOrder.update_work_order_qty = update_work_order_qty
WorkOrder.update_transaferred_qty_for_required_items = update_transaferred_qty_for_required_items
WorkOrder.update_consumed_qty_for_required_items = update_consumed_qty_for_required_items


#payment term override
from chemical.api import get_due_date
from erpnext.controllers import accounts_controller
accounts_controller.get_due_date = get_due_date

# overide reason bcz raw material changes on change event of fg_completed_qty
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from chemical.chemical.doc_events.work_order import get_items
StockEntry.get_items = get_items

# import erpnext
# erpnext.stock.utils.get_incoming_rate = my_incoming_rate

#quality inspection override for sample
from erpnext.stock.doctype.quality_inspection.quality_inspection import QualityInspection
from chemical.chemical.doc_events.quality_inspection import update_qc_reference
QualityInspection.update_qc_reference = update_qc_reference

app_name = "chemical"
app_title = "Chemical"
app_publisher = "FinByz Tech Pvt. Ltd."
app_description = "Custom App for chemical Industry"
app_icon = "octicon octicon-beaker"
app_color = "Orange"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/chemical/css/chemical.css"
# app_include_js = "/assets/chemical/js/chemical.js"

# app_include_js = [
# 	"assets/js/summernote.min.js",
# 	"assets/js/comment_desk.min.js",
# 	"assets/js/editor.min.js",
# 	"assets/js/timeline.min.js"
# ]

# fixtures = ["Custom Field"]

# app_include_css = [
# 	"assets/css/summernote.min.css"
# ]

# include js, css files in header of web template
# web_include_css = "/assets/chemical/css/chemical.css"
# web_include_js = "/assets/chemical/js/chemical.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
	"BOM": "public/js/doctype_js/bom.js",
	"BOM Update Tool": "public/js/doctype_js/bom_update_tool.js",
	"Stock Entry": "public/js/doctype_js/stock_entry.js",
	"Purchase Invoice": "public/js/doctype_js/purchase_invoice.js",
	"Purchase Order": "public/js/doctype_js/purchase_order.js",
	"Work Order": "public/js/doctype_js/work_order.js",
	"Sales Order": "public/js/doctype_js/sales_order.js",
	"Sales Invoice": "public/js/doctype_js/sales_invoice.js",
	"Delivery Note": "public/js/doctype_js/delivery_note.js",
	"Address": "public/js/doctype_js/address.js",
	"Customer": "public/js/doctype_js/customer.js",
	"Supplier": "public/js/doctype_js/supplier.js",
	"Production Plan": "public/js/doctype_js/production_plan.js",
	"Purchase Receipt": "public/js/doctype_js/purchase_receipt.js",
	"Item": "public/js/doctype_js/item.js",
	"Batch": "public/js/doctype_js/batch.js",
	"Quotation":"public/js/doctype_js/quotation.js",
	"Quality Inspection":"public/js/doctype_js/quality_inspection.js",
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "chemical.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "chemical.install.before_install"
# after_install = "chemical.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "chemical.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"chemical.tasks.all"
# 	],
# 	"daily": [
# 		"chemical.tasks.daily"
# 	],
# 	"hourly": [
# 		"chemical.tasks.hourly"
# 	],
# 	"weekly": [
# 		"chemical.tasks.weekly"
# 	]
# 	"monthly": [
# 		"chemical.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "chemical.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#


#fixtures = ["Custom Field"]

# after_migrate = [
# 	'frappe.website.doctype.website_theme.website_theme.generate_theme_files_if_not_exist'
# ]

override_whitelisted_methods = {
	"erpnext.manufacturing.doctype.bom_update_tool.bom_update_tool.enqueue_update_cost": "chemical.chemical.doc_events.bom.enqueue_update_cost",
	"erpnext.stock.doctype.stock_reconciliation.stock_reconciliation.get_stock_balance_for": "chemical.chemical.doc_events.stock_reconciliation.get_stock_balance_for"
}

doc_events = {
	"BOM": {
		"before_save": "chemical.chemical.doc_events.bom.bom_before_save",
		"validate": "chemical.chemical.doc_events.bom.bom_validate",
		"on_submit":"chemical.chemical.doc_events.bom.on_submit"
	},
	"Item Price": {
		"before_save": "chemical.chemical.doc_events.item_price.before_save",
	},
	"Customer":{
		"before_rename": "chemical.chemical.doc_events.customer.customer_override_after_rename",
		"autoname": "chemical.chemical.doc_events.customer.customer_auto_name",
	},
	"Supplier":{
		"before_rename": "chemical.chemical.doc_events.supplier.supplier_override_after_rename",
		"autoname": "chemical.chemical.doc_events.supplier.supplier_auto_name",
	},
	"Item": {
		"validate": "chemical.chemical.doc_events.item.item_validate",
	},
	"Work Order":{
		"validate":"chemical.chemical.doc_events.work_order.validate",
		"before_submit": "chemical.chemical.doc_events.work_order.before_submit",
	},
	"Stock Entry": {
		"onload": "chemical.chemical.doc_events.stock_entry.onload",
		"before_validate": "chemical.chemical.doc_events.stock_entry.before_validate",
		"validate": [
			"chemical.chemical.doc_events.stock_entry.stock_entry_validate",
			"chemical.batch_valuation.stock_entry_validate",
			"chemical.chemical.doc_events.stock_entry.validate",
		],
		"before_save": [
			 "chemical.chemical.doc_events.stock_entry.stock_entry_before_save",
		],
		"before_submit": [
			"chemical.chemical.doc_events.stock_entry.se_before_submit",
			"chemical.chemical.doc_events.stock_entry.before_submit",
		],
		"on_submit": [
			"chemical.batch_valuation.stock_entry_on_submit",
			"chemical.chemical.doc_events.stock_entry.stock_entry_on_submit",
		],
		"before_cancel":[
			"chemical.chemical.doc_events.stock_entry.se_before_cancel",
			"chemical.api.stock_entry_before_cancel",
		],
		"on_cancel": [
			"chemical.chemical.doc_events.stock_entry.stock_entry_on_cancel",
			"chemical.chemical.doc_events.stock_entry.on_cancel",
			"chemical.batch_valuation.stock_entry_on_cancel",
		],
		"on_update_after_submit": [
			"chemical.chemical.doc_events.stock_entry.on_update_after_submit",
		]
	},
	"Batch": {
		'before_naming': "chemical.batch_valuation.override_batch_autoname",
	},
	"Purchase Receipt": {
		"onload":"chemical.chemical.doc_events.purchase_receipt.onload",
		"before_validate": "chemical.chemical.doc_events.purchase_receipt.before_validate",
		"validate": [
			# "chemical.api.pr_validate",
			"chemical.batch_valuation.pr_validate",
			"chemical.chemical.doc_events.purchase_receipt.t_validate",
		],
		"on_cancel": "chemical.batch_valuation.pr_on_cancel",
		"before_submit": "chemical.chemical.doc_events.purchase_receipt.before_submit",
		"before_cancel": "chemical.chemical.doc_events.purchase_receipt.before_cancel",
	},
	"Purchase Invoice": {
		"onload":"chemical.chemical.doc_events.purchase_invoice.onload",
		"before_validate": "chemical.chemical.doc_events.purchase_invoice.before_validate",
		"validate": [
			"chemical.batch_valuation.pi_validate",
		],
		"on_cancel": "chemical.batch_valuation.pi_on_cancel",
		"before_submit": "chemical.chemical.doc_events.purchase_invoice.before_submit",
		"before_cancel": "chemical.chemical.doc_events.purchase_invoice.before_cancel",
		"on_trash":"chemical.chemical.doc_events.purchase_invoice.on_trash",

	},
	"Purchase Order": {
		"onload":"chemical.chemical.doc_events.purchase_order.onload",
		"validate": "chemical.chemical.doc_events.purchase_order.validate"
	},
	
	"Landed Cost Voucher": {
		"validate": [
			"chemical.batch_valuation.lcv_validate",
			# "chemical.api.lcv_validate",
		],
		"on_submit": "chemical.batch_valuation.lcv_on_submit",
		"on_cancel": [
			"chemical.batch_valuation.lcv_on_cancel",
		],
	},
	"Delivery Note": {
		"onload":"chemical.chemical.doc_events.delivery_note.onload",
		"on_submit": "chemical.chemical.doc_events.delivery_note.dn_on_submit",
		"before_cancel": "chemical.chemical.doc_events.delivery_note.before_cancel",
		"before_submit": "chemical.chemical.doc_events.delivery_note.before_submit",

		"validate": "chemical.chemical.doc_events.delivery_note.validate",
	},
	"Sales Invoice": {
		"onload":"chemical.chemical.doc_events.sales_invoice.onload",
		"before_submit": [
			"chemical.chemical.doc_events.sales_invoice.si_before_submit",
			"chemical.chemical.doc_events.sales_invoice.before_submit",
		],
		"before_validate": "chemical.chemical.doc_events.sales_invoice.before_validate",
		"validate": "chemical.chemical.doc_events.sales_invoice.validate",
		"before_cancel": "chemical.chemical.doc_events.sales_invoice.before_cancel",
		"on_trash":"chemical.chemical.doc_events.sales_invoice.on_trash",

	},
	"Stock Ledger Entry": {
		"before_submit": "chemical.chemical.doc_events.stock_ledger_entry.sl_before_submit"
	},
	"Stock Reconciliation":{
		"on_submit":"chemical.chemical.doc_events.stock_reconciliation.on_submit",
		"on_cancel":"chemical.chemical.doc_events.stock_reconciliation.on_cancel"
	},
	"Sales Order": {
		"onload":"chemical.chemical.doc_events.sales_order.onload",
		"on_cancel": "chemical.api.so_on_cancel",
		"before_validate": "chemical.chemical.doc_events.sales_order.validate"
	},
	("Outward Sample","Ball Mill Data Sheet","Outward Tracking"):{
		"on_submit":"chemical.chemical.doc_events.outward_sample.on_submit",
		"before_update_after_submit":"chemical.chemical.doc_events.outward_sample.before_update_after_submit",
		"before_cancel":"chemical.chemical.doc_events.outward_sample.on_cancel",
		"on_trash":"chemical.chemical.doc_events.outward_sample.on_trash"
	},
}

scheduler_events = {
	"daily":[
		"chemical.chemical.doc_events.bom.update_item_price_daily"
	]
}

override_doctype_dashboards = {
	"Stock Entry": "chemical.chemical.dashboard.stock_entry.get_data",
	"Customer": "chemical.chemical.dashboard.customer.get_data",
	"Quotation": "chemical.chemical.dashboard.quotation.get_data",
	"Lead": "chemical.chemical.dashboard.lead.get_data"
}

#Work Order Summary Report Override From Finbyz Dashboard For Chart
# from chemical.chemical.report.work_order_summary import execute as wos_execute
# from finbyz_dashboard.finbyz_dashboard.report.work_order_summary import work_order_summary
# work_order_summary.execute = wos_execute


# Chemical Overrides

from chemical.batch_valuation_overrides import get_supplied_items_cost,set_incoming_rate_buying,set_incoming_rate_selling,get_rate_for_return,get_incoming_rate,process_sle,get_args_for_incoming_rate

# Buying controllers
from erpnext.controllers.buying_controller import BuyingController
BuyingController.get_supplied_items_cost = get_supplied_items_cost
BuyingController.set_incoming_rate = set_incoming_rate_buying

# Selling controllers
from erpnext.controllers.selling_controller import SellingController
SellingController.set_incoming_rate = set_incoming_rate_selling

# sales and purchase return
from erpnext.controllers import sales_and_purchase_return
sales_and_purchase_return.get_rate_for_return =  get_rate_for_return

# utils

# from erpnext.stock import utils
# utils.get_incoming_rate =  get_incoming_rate

import erpnext
erpnext.stock.utils.get_incoming_rate = get_incoming_rate

# stock_ledger
from erpnext.stock.stock_ledger import update_entries_after
update_entries_after.process_sle =  process_sle

# stock entry
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
StockEntry.get_args_for_incoming_rate = get_args_for_incoming_rate

from erpnext.stock.doctype.stock_reconciliation import stock_reconciliation
from chemical.chemical.doc_events.stock_reconciliation import get_stock_balance_for
stock_reconciliation.get_stock_balance_for = get_stock_balance_for