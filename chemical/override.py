from __future__ import unicode_literals
from . import  __version__ as app_version

from erpnext.accounts.doctype.opening_invoice_creation_tool.opening_invoice_creation_tool import OpeningInvoiceCreationTool
from chemical.chemical.doc_events.opening_invoice_creation_tool import get_invoice_dict, make_invoices

OpeningInvoiceCreationTool.get_invoice_dict = get_invoice_dict
OpeningInvoiceCreationTool.make_invoices = make_invoices

import erpnext
#from chemical.batch_valuation_overrides import get_incoming_rate as my_incoming_rate, process_sle as my_process_sle, get_args_for_incoming_rate as my_get_args_for_incoming_rate, update_raw_materials_supplied_based_on_bom as my_update_raw_materials_supplied_based_on_bom, update_stock_ledger as my_update_stock_ledger
from erpnext.stock.stock_ledger import update_entries_after


def override_functions():
	pass
	#print("Overriding functions...")
	# erpnext.stock.utils.get_incoming_rate = my_incoming_rate
	# update_entries_after.process_sle = my_process_sle
	# StockEntry.get_args_for_incoming_rate = my_get_args_for_incoming_rate
	# BuyingController.update_raw_materials_supplied_based_on_bom = my_update_raw_materials_supplied_based_on_bom
	# SellingController.update_stock_ledger = my_update_stock_ledger