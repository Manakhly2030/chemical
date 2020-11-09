from __future__ import unicode_literals

import frappe
import frappe.defaults
from frappe import _
from frappe import msgprint, _
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
#from frappe.utils.background_jobs import enqueue
#from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.desk.notifications import get_filters_for
from datetime import date

from erpnext.stock.stock_ledger import update_entries_after

# from erpnext.selling.doctype.customer.customer import Customer
# from erpnext.buying.doctype.supplier.supplier import Supplier
# from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
# from erpnext.manufacturing.doctype.work_order.work_order import get_item_details	
# from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan

#from erpnext.manufacturing.doctype.bom.bom import add_additional_cost

#import json
#from six import itervalues, string_types

@frappe.whitelist()
def get_customer_ref_code(item_code, customer):
	ref_code = frappe.db.get_value("Item Customer Detail", {'parent': item_code, 'customer_name': customer}, 'ref_code')
	return ref_code if ref_code else ''

@frappe.whitelist()
def get_supplier_ref_code(item_code, supplier):

	ref_code = frappe.db.get_value("Item Supplier", {'parent': item_code, 'supplier': supplier}, 'supplier_part_no')	
	return ref_code 


@frappe.whitelist()
def get_party_details(party=None, party_type="Customer", ignore_permissions=True):

	if not party:
		return {}

	if not frappe.db.exists(party_type, party):
		frappe.throw(_("{0}: {1} does not exists").format(party_type, party))

	return _get_party_details(party, party_type, ignore_permissions)

def _get_party_details(party=None, party_type="Customer", ignore_permissions=True):

	out = frappe._dict({
		party_type.lower(): party
	})

	party = out[party_type.lower()]

	if not ignore_permissions and not frappe.has_permission(party_type, "read", party):
		frappe.throw(_("Not permitted for {0}").format(party), frappe.PermissionError)

	party = frappe.get_doc(party_type, party)
	
	set_address_details(out, party, party_type)
	set_contact_details(out, party, party_type)
	set_other_values(out, party, party_type)
	set_organization_details(out, party, party_type)
	return out

def set_address_details(out, party, party_type):
	billing_address_field = "customer_address" if party_type == "Lead" \
		else party_type.lower() + "_address"
	out[billing_address_field] = get_default_address(party_type, party.name)
	
	# address display
	out.address_display = get_address_display(out[billing_address_field])


def set_contact_details(out, party, party_type):
	out.contact_person = get_default_contact(party_type, party.name)

	if not out.contact_person:
		out.update({
			"contact_person": None,
			"contact_display": None,
			"contact_email": None,
			"contact_mobile": None,
			"contact_phone": None,
			"contact_designation": None,
			"contact_department": None
		})
	else:
		out.update(get_contact_details(out.contact_person))

def set_other_values(out, party, party_type):
	# copy
	if party_type=="Customer":
		to_copy = ["customer_name", "customer_group", "territory", "language"]
	else:
		to_copy = ["supplier_name", "supplier_type", "language"]
	for f in to_copy:
		out[f] = party.get(f)
		
def set_organization_details(out, party, party_type):

	organization = None

	if party_type == 'Lead':
		organization = frappe.db.get_value("Lead", {"name": party.name}, "company_name")
	elif party_type == 'Customer':
		organization = frappe.db.get_value("Customer", {"name": party.name}, "customer_name")
	elif party_type == 'Supplier':
		organization = frappe.db.get_value("Supplier", {"name": party.name}, "supplier_name")

	out.update({'party_name': organization})

def update_po_volume(self, po, ignore_permissions = True):
	if self._action == 'submit':
		po.save(ignore_permissions = True)

	elif self._action == 'cancel':
		po.db_set('batch','')
		po.save(ignore_permissions=True)

def stock_entry_before_cancel(self,method):
	if self.work_order:
		pro_doc = frappe.get_doc("Work Order", self.work_order)
		pro_doc.db_set('batch','')
		set_po_status(self, pro_doc)
		update_po_volume(self, pro_doc)
		pro_doc.save()
		#frappe.db.commit()

def cal_rate_qty(self):
	for d in self.items:
		maintain_as_is_stock = frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock')
		if maintain_as_is_stock:
			if not d.concentration and d.t_warehouse:
				frappe.throw("{} Row: {} Please add concentration".format(d.doctype,d.idx))
			concentration = 0.0
			if d.get('batch_no'):
				concentration = frappe.db.get_value("Batch",d.batch_no,"concentration")
			else:
				concentration = d.concentration
		if d.get('packing_size') and d.get('no_of_packages'):
			d.qty = d.packing_size * d.no_of_packages
			if maintain_as_is_stock:
				if d.get('batch_no'):
					concentration = frappe.db.get_value("Batch",d.batch_no,"concentration")
				else:
					concentration = d.concentration
				d.quantity = d.qty * concentration / 100
				if d.price:
					d.rate =  flt(d.quantity * d.price) / flt(d.qty)
			else:
				d.quantity = d.qty
				if d.price:
					d.rate= d.price
		else:
			if maintain_as_is_stock:
				if d.quantity:
					d.qty = flt((d.quantity * 100.0) / d.concentration)
				if d.price:
					d.rate =  flt(d.quantity * d.price) / flt(d.qty)
			else:
				if d.quantity:
					d.qty = d.quantity
				if d.price:
					d.rate= d.price

def purchase_cal_rate_qty(self):
	for d in self.items:
		doctype_items = ''
		if self.doctype == "Purchase Receipt":
			doctype_items = "Purchase Receipt Item"
		if self.doctype == "Purchase Invoice":
			doctype_items = "Purchase Invoice Item"
		if self.doctype == "Stock Entry":
			doctype_items = "Stock Entry Detail"
		doc_items = frappe.get_doc({"doctype":doctype_items}) 
		maintain_as_is_stock = frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock')
		packing_size = 0

		if hasattr(doc_items,'receive_qty'):
			if hasattr(doc_items,'tare_weight'):
				if hasattr(doc_items, 'receive_packing_size') and hasattr(doc_items, 'receive_no_of_packages'):
					packing_size = flt(d.receive_packing_size) - flt(d.tare_weight)
					d.receive_qty =  flt(packing_size) * flt(d.receive_no_of_packages)
			else:
				if hasattr(doc_items, 'receive_packing_size') and hasattr(doc_items, 'receive_no_of_packages'):
					packing_size = flt(d.receive_packing_size)
					d.receive_qty =  flt(packing_size) * flt(d.receive_no_of_packages)				
		else:
			if d.packing_size and d.no_of_packages:
				d.qty = received_qty = flt(d.packing_size) * flt(d.no_of_packages)

		if hasattr(doc_items,'accepted_qty'):
			if hasattr(doc_items, 'accepted_packing_size') and hasattr(doc_items, 'accepted_no_of_packages'):
				d.accepted_qty = flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages)
		
		if hasattr(doc_items,'supplier_qty'):
			if hasattr(doc_items, "supplier_packing_size") and hasattr(doc_items, "supplier_no_of_packages"):
				d.supplier_qty = flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages)
			if not d.supplier_qty:
				frappe.throw("{} Row: {} Please add supplier Qty".format(d.doctype,d.idx))

		if hasattr(doc_items,'receive_packing_size'):
				if hasattr(doc_items,'accepted_packing_size'):
					d.packing_size = flt(d.accepted_packing_size) or flt(packing_size)
					d.no_of_packages = flt(d.accepted_no_of_packages) or flt(d.receive_no_of_packages)
				else:
					d.packing_size = flt(packing_size)
					d.no_of_packages = flt(d.receive_no_of_packages)
			

		if maintain_as_is_stock:
			if hasattr(doc_items,'received_concentration'):
				d.receive_quantity = flt(d.receive_qty) * flt(d.received_concentration) / 100
			if hasattr(doc_items,'supplier_concentration'):
				if not d.supplier_concentration:
					frappe.throw("{} Row: {} Please add supplier concentration".format(d.doctype,d.idx))
				d.supplier_quantity = flt(d.supplier_qty) * flt(d.supplier_concentration) / 100
			if hasattr(doc_items,'accepted_concentration'):
				d.accepted_quantity = flt(d.accepted_qty) * flt(d.accepted_concentration) / 100

			if hasattr(doc_items,'accepted_qty') and hasattr(doc_items,'receive_qty'):
				d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
			if hasattr(doc_items,'accepted_concentration') and hasattr(doc_items,'received_concentration'): 
				d.concentration = flt(d.accepted_concentration) or flt(d.received_concentration)
			
			if not hasattr(doc_items,'receive_qty') and (not d.packing_size or not d.no_of_packages):
				if d.quantity:
					d.qty = flt((d.quantity * 100.0) / d.concentration)

			if not d.qty:
				if hasattr(doc_items,'receive_qty'):
					frappe.throw("{} Row: {} Please add Receive Qty or Accepted Qty".format(d.doctype,d.idx))
				else:
					frappe.throw("{} Row: {} Please add Qty".format(d.doctype,d.idx))
			if not d.concentration:
				if hasattr(doc_items,'received_concentration'):
					frappe.throw("{} Row: {} Please add received or accepted concentration".format(d.doctype,d.idx))
				else:
					frappe.throw("{} Row: {} Please add concentration".format(d.doctype,d.idx))
			
			if hasattr(doc_items,'accepted_quantity') and hasattr(doc_items,'receive_quantity'):
				d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)	
			else:
				d.quantity = flt(d.qty)*flt(d.concentration)/100

			if hasattr(doc_items,'supplier_quantity'):
				d.rate = flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)
			else:
				d.rate = flt(d.quantity) * flt(d.price) / flt(d.qty)

		else:
			if hasattr(doc_items,'received_concentration'):
				d.receive_quantity = flt(d.receive_qty)
			if hasattr(doc_items,'supplier_concentration'):
				d.supplier_quantity = flt(d.supplier_qty)
			if hasattr(doc_items,'accepted_concentration'):
				d.accepted_quantity = flt(d.accepted_qty)

			if hasattr(doc_items,'accepted_qty') and hasattr(doc_items,'receive_qty'):
				d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
			if hasattr(doc_items,'accepted_concentration') and hasattr(doc_items,'received_concentration'): 
				d.concentration = flt(d.accepted_concentration) or flt(d.received_concentration)
			
			if not hasattr(doc_items,'receive_qty') and (not d.packing_size or not d.no_of_packages):
				if d.quantity:
					d.qty = flt(d.quantity)

			if not d.qty:
				if hasattr(doc_items,'receive_qty'):
					frappe.throw("{} Row: {} Please add Receive Qty or Accepted Qty".format(d.doctype,d.idx))
				else:
					frappe.throw("{} Row: {} Please add Qty".format(d.doctype,d.idx))
					
			if hasattr(doc_items,'accepted_quantity') and hasattr(doc_items,'receive_quantity'):
				d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)	
			else:
				d.quantity = flt(d.qty) 
			
				
			d.rate = flt(d.price)
					

		if hasattr(doc_items,'short_quantity'):
			d.short_quantity = flt(d.quantity) - flt(d.supplier_quantity)
			if d.short_quantity:
				d.rate = flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)

		if hasattr(doc_items,'amount_difference'):
			d.amount_difference = flt(d.price) * flt(d.short_quantity) 

def se_repack_cal_rate_qty(self):
	for d in self.items:
		doc_items = frappe.get_doc({"doctype":"Stock Entry Detail"}) 
		maintain_as_is_stock = frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock')
		packing_size = 0
		if not d.s_warehouse:
			if hasattr(doc_items,'receive_qty'):
				if hasattr(doc_items,'tare_weight'):
					if hasattr(doc_items, 'receive_packing_size') and hasattr(doc_items, 'receive_no_of_packages'):
						packing_size = flt(d.receive_packing_size) - flt(d.tare_weight)
						d.receive_qty =  flt(packing_size) * flt(d.receive_no_of_packages)
				else:
					if hasattr(doc_items, 'receive_packing_size') and hasattr(doc_items, 'receive_no_of_packages'):
						packing_size = flt(d.receive_packing_size)
						d.receive_qty =  flt(packing_size) * flt(d.receive_no_of_packages)				
			else:
				if d.packing_size and d.no_of_packages:
					d.qty = received_qty = flt(d.packing_size) * flt(d.no_of_packages)

			if hasattr(doc_items,'accepted_qty'):
				if hasattr(doc_items, 'accepted_packing_size') and hasattr(doc_items, 'accepted_no_of_packages'):
					d.accepted_qty = flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages)
			
			if hasattr(doc_items,'supplier_qty'):
				if hasattr(doc_items, "supplier_packing_size") and hasattr(doc_items, "supplier_no_of_packages"):
					d.supplier_qty = flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages)
				if not d.supplier_qty:
					frappe.throw("{} Row: {} Please add supplier Qty".format(d.doctype,d.idx))

			if hasattr(doc_items,'receive_packing_size'):
					if hasattr(doc_items,'accepted_packing_size'):
						d.packing_size = flt(d.accepted_packing_size) or flt(packing_size)
						d.no_of_packages = flt(d.accepted_no_of_packages) or flt(d.receive_no_of_packages)
					else:
						d.packing_size = flt(packing_size)
						d.no_of_packages = flt(d.receive_no_of_packages)
				

			if maintain_as_is_stock:
				if hasattr(doc_items,'received_concentration'):
					d.receive_quantity = flt(d.receive_qty) * flt(d.received_concentration) / 100
				if hasattr(doc_items,'supplier_concentration'):
					if not d.supplier_concentration:
						frappe.throw("{} Row: {} Please add supplier concentration".format(d.doctype,d.idx))
					d.supplier_quantity = flt(d.supplier_qty) * flt(d.supplier_concentration) / 100
				if hasattr(doc_items,'accepted_concentration'):
					d.accepted_quantity = flt(d.accepted_qty) * flt(d.accepted_concentration) / 100

				if hasattr(doc_items,'accepted_qty') and hasattr(doc_items,'receive_qty'):
					d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
				if hasattr(doc_items,'accepted_concentration') and hasattr(doc_items,'received_concentration'): 
					d.concentration = flt(d.accepted_concentration) or flt(d.received_concentration)
				
				if not d.qty:
					if hasattr(doc_items,'receive_qty'):
						frappe.throw("{} Row: {} Please add Receive Qty or Accepted Qty".format(d.doctype,d.idx))
					else:
						frappe.throw("{} Row: {} Please add Qty".format(d.doctype,d.idx))
				if not d.concentration:
					if hasattr(doc_items,'received_concentration'):
						frappe.throw("{} Row: {} Please add received or accepted concentration".format(d.doctype,d.idx))
					else:
						frappe.throw("{} Row: {} Please add concentration".format(d.doctype,d.idx))
				
				if hasattr(doc_items,'accepted_quantity') and hasattr(doc_items,'receive_quantity'):
					d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)	
				else:
					d.quantity = flt(d.qty)*flt(d.concentration)/100
				if hasattr(doc_items,'supplier_quantity'):
					d.basic_rate= flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)

			else:
				if hasattr(doc_items,'received_concentration'):
					d.receive_quantity = flt(d.receive_qty)
				if hasattr(doc_items,'supplier_concentration'):
					d.supplier_quantity = flt(d.supplier_qty)
				if hasattr(doc_items,'accepted_concentration'):
					d.accepted_quantity = flt(d.accepted_qty)

				if hasattr(doc_items,'accepted_qty') and hasattr(doc_items,'receive_qty'):
					d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
				if hasattr(doc_items,'accepted_concentration') and hasattr(doc_items,'received_concentration'): 
					d.concentration = flt(d.accepted_concentration) or flt(d.received_concentration)
				
				if not d.qty:
					if hasattr(doc_items,'receive_qty'):
						frappe.throw("{} Row: {} Please add Receive Qty or Accepted Qty".format(d.doctype,d.idx))
					else:
						frappe.throw("{} Row: {} Please add Qty".format(d.doctype,d.idx))
						
				if hasattr(doc_items,'accepted_quantity') and hasattr(doc_items,'receive_quantity'):
					d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)	
				else:
					d.quantity = flt(d.qty) 

				d.basic_rate= flt(d.price)
						

			if hasattr(doc_items,'short_quantity'):
				d.short_quantity = flt(d.quantity) - flt(d.supplier_quantity)
				if d.short_quantity:
					d.rate = flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)

			if hasattr(doc_items,'amount_difference'):
				d.amount_difference = flt(d.price) * flt(d.short_quantity)

		else:
			if maintain_as_is_stock:
				if not d.concentration and d.t_warehouse:
					frappe.throw("{} Row: {} Please add concentration".format(d.doctype,d.idx))
				concentration = 0.0
				if d.batch_no:
					concentration = frappe.db.get_value("Batch",d.batch_no,"concentration")
				else:
					concentration = d.concentration
			if d.get('packing_size') and d.get('no_of_packages'):
				d.qty = (d.packing_size * d.no_of_packages)
				if maintain_as_is_stock:
					d.quantity = d.qty * concentration / 100
					if d.price:
						d.basic_rate =  flt(d.quantity) * flt(d.price) / flt(d.qty)
				else:
					d.quantity = d.qty
					if d.price:
						d.basic_rate = d.price
			else:
				if maintain_as_is_stock:
					if d.quantity:
						d.qty = flt((d.quantity * 100.0) / concentration)
					if d.price:
						d.basic_rate =  flt(d.quantity) * flt(d.price) / flt(d.qty)
				else:
					if d.quantity:
						d.qty = d.quantity
					if d.price:
						d.basic_rate = d.price
			

def se_cal_rate_qty(self):
	doc_items = frappe.get_doc({"doctype":"Stock Entry Detail"})
	for d in self.items:
		maintain_as_is_stock = frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock')
		if maintain_as_is_stock:
			if not d.concentration and d.t_warehouse:
				frappe.throw("{} Row: {} Please add concentration".format(d.doctype,d.idx))
			concentration = 0.0
			if d.batch_no:
				concentration = frappe.db.get_value("Batch",d.batch_no,"concentration")
			else:
				concentration = d.concentration
		if d.get('packing_size') and d.get('no_of_packages'):
			d.qty = (d.packing_size * d.no_of_packages)
			if maintain_as_is_stock:
				d.quantity = d.qty * concentration / 100
				if d.price:
					d.basic_rate =  flt(d.quantity) * flt(d.price) / flt(d.qty)
			else:
				d.quantity = d.qty
				if d.price:
					d.basic_rate = d.price
		else:
			if maintain_as_is_stock:
				if d.quantity:
					d.qty = flt((d.quantity * 100.0) / concentration)
				if d.price:
					d.basic_rate =  flt(d.quantity) * flt(d.price) / flt(d.qty)
			else:
				if d.quantity:
					d.qty = d.quantity
				if d.price:
					d.basic_rate = d.price

def cal_actual_valuations(self):
	for row in self.items:
		maintain_as_is_stock = frappe.db.get_value("Items",row.item_code,"maintain_as_is_stock")
		if maintain_as_is_stock:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt((flt(row.valuation_rate)*100)/concentration)
		else:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt(row.valuation_rate)

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)

@frappe.whitelist()
def dn_before_cancel(self, method):
	update_sales_invoice(self)

def so_on_cancel(self, method):
	pass
	
def update_outward_sample(self) :
	for row in self.items:
		if row.outward_sample:
			os_doc = frappe.get_doc("Outward Sample",row.outward_sample)
			os_doc.db_set('sales_order', '')

@frappe.whitelist()
def get_actual_and_projected_qty(warehouse,item_code):
	qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse},["projected_qty", "actual_qty"], as_dict=True, cache=True)
	return qty['actual_qty'] ,qty['projected_qty']


# show Sample count on customer and supplier dashboard
# call it on customer and supplier js
@frappe.whitelist()
def get_open_count(doctype, name, links):
	'''Get open count for given transactions and filters

	:param doctype: Reference DocType
	:param name: Reference Name
	:param transactions: List of transactions (json/dict)
	:param filters: optional filters (json/list)'''

	frappe.has_permission(doc=frappe.get_doc(doctype, name), throw=True)

	meta = frappe.get_meta(doctype)
	#links = meta.get_dashboard_data()

	links = frappe._dict({
		'fieldname': 'party',
		'transactions': [
			{
				'label': _('Outward Sample'),
				'items': ['Outward Sample']
			},
			{
				'label': _('Inward Sample'),
				'items': ['Inward Sample']
			},
		]
	})
	#frappe.msgprint(str(links))
	#links = frappe._dict(links)
	#return {'count':0}


	# compile all items in a list
	items = []
	for group in links.transactions:
		items.extend(group.get('items'))

	out = []
	for d in items:
		if d in links.get('internal_links', {}):
			# internal link
			continue

		filters = get_filters_for(d)
		fieldname = links.get('non_standard_fieldnames', {}).get(d, links.fieldname)
		#return fieldname
		data = {'name': d}
		if filters:
			# get the fieldname for the current document
			# we only need open documents related to the current document
			filters[fieldname] = name
			total = len(frappe.get_all(d, fields='name',
				filters=filters, limit=100, distinct=True, ignore_ifnull=True))
			data['open_count'] = total

		total = len(frappe.get_all(d, fields='name',
			filters={fieldname: name}, limit=100, distinct=True, ignore_ifnull=True))
		data['count'] = total
		out.append(data)

	out = {
		'count': out,
	}

	module = frappe.get_meta_module(doctype)
	if hasattr(module, 'get_timeline_data'):
		out['timeline_data'] = module.get_timeline_data(doctype, name)
	
	return out

def check_sub(string, sub_str): 
	if (string.find(sub_str) == -1): 
	   return False 
	else: 
		return True


def get_fiscal(date):
	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

	return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]

def quantity_price_to_qty_rate(self):
	for item in self.items:
		has_batch_no,maintain_as_is_stock = frappe.db.get_value('Item', item.item_code, ['has_batch_no','maintain_as_is_stock'])
		concentration = item.get('concentration') or 100
		if item.qty and item.quantity == 0:
			if maintain_as_is_stock:
				item.db_set("quantity",flt(item.qty)*flt(concentration)/100)
			else:
				item.db_set("quantity",flt(item.qty))
		if item.rate and item.price ==0:
			if maintain_as_is_stock:
				item.db_set("price",flt(item.rate)*100/concentration)
			else:
				item.db_set("price",flt(item.rate))
								
