# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

from erpnext.accounts.doctype.opening_invoice_creation_tool.opening_invoice_creation_tool import OpeningInvoiceCreationTool
from chemical.chemical.doc_events.opening_invoice_creation_tool import get_invoice_dict, make_invoices

OpeningInvoiceCreationTool.get_invoice_dict = get_invoice_dict
OpeningInvoiceCreationTool.make_invoices = make_invoices

import erpnext
erpnext.stock.utils.get_incoming_rate = my_incoming_rate

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

fixtures = ["Custom Field"]

app_include_css = [
	"assets/css/summernote.min.css"
]

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
override_whitelisted_methods = {
	"erpnext.education.api.enroll_student": "chemical.api.test"
}

#fixtures = ["Custom Field"]

# after_migrate = [
# 	'frappe.website.doctype.website_theme.website_theme.generate_theme_files_if_not_exist'
# ]

override_whitelisted_methods = {
	"erpnext.manufacturing.doctype.bom_update_tool.bom_update_tool.enqueue_update_cost": "chemical.chemical.doc_events.bom.enqueue_update_cost",
}

doc_events = {
	"BOM": {
		"before_save": "chemical.chemical.doc_events.bom.bom_before_save",
		"validate": "chemical.chemical.doc_events.bom.bom_validate"	
	},
	# "Item Price": {
	# 	"before_save": "chemical.api.IP_before_save",
	# },
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
	"Stock Entry": {
		"validate": [
			# "chemical.chemical.doc_events.stock_entry.stock_entry_validate",
			"chemical.batch_valuation.stock_entry_validate",
		],
		"before_save": "chemical.chemical.doc_events.stock_entry.stock_entry_before_save",
		"before_insert": "chemical.chemical.doc_events.stock_entry.before_insert",
		"before_submit": "chemical.chemical.doc_events.stock_entry.se_before_submit",
		"on_submit": [
			"chemical.chemical.doc_events.stock_entry.stock_entry_on_submit",
			"chemical.batch_valuation.stock_entry_on_submit",
		],
		"before_cancel": "chemical.chemical.doc_events.stock_entry.se_before_cancel",
		"on_cancel": [
			"chemical.chemical.doc_events.stock_entry.stock_entry_on_cancel",
			"chemical.batch_valuation.stock_entry_on_cancel",
		],
	},
	"Batch": {
		'before_naming': "chemical.batch_valuation.override_batch_autoname",
	},
	"Purchase Receipt": {
		"validate": [
			# "chemical.api.pr_validate",
			"chemical.batch_valuation.pr_validate",
		],
		"on_cancel": "chemical.batch_valuation.pr_on_cancel",
	},
	"Purchase Invoice": {
		"before_insert": "chemical.chemical.doc_events.purchase_invoice.before_insert",
		"validate": "chemical.batch_valuation.pi_validate",
		"on_cancel": "chemical.batch_valuation.pi_on_cancel",
	},
	"Landed Cost Voucher": {
		"validate": [
			"chemical.batch_valuation.lcv_validate",
			"chemical.api.lcv_validate",
		],
		"on_submit": "chemical.batch_valuation.lcv_on_submit",
		"on_cancel": [
			"chemical.batch_valuation.lcv_on_cancel",
		],
	},
	"Delivery Note": {
		"on_submit": "chemical.chemical.doc_events.delivery_note.dn_on_submit",
		#"before_cancel": "chemical.chemical.doc_events.delivery_note.dn_before_cancel",
	},
	"Sales Invoice": {
		"before_insert": "chemical.chemical.doc_events.sales_invoice.before_insert",
		"before_submit": "chemical.chemical.doc_events.sales_invoice.si_before_submit"
	},
	"Stock Ledger Entry": {
		"before_submit": "chemical.chemical.doc_events.stock_ledger_entry.sl_before_submit"
	},
	"Sales Order": {
		"on_cancel": "chemical.api.so_on_cancel"
	},
}

scheduler_events = {
	"daily":[
		"chemical.chemical.doc_events.bom.update_item_price_daily"
	]
}

