from __future__ import unicode_literals
import frappe
import json
import frappe.defaults
from frappe import _, db
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.contacts.doctype.address.address import get_address_display, get_default_address
from frappe.contacts.doctype.contact.contact import get_contact_details, get_default_contact
from frappe.utils import nowdate,flt,cint
from frappe.utils.background_jobs import enqueue
from erpnext.selling.doctype.customer.customer import Customer
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.buying.doctype.supplier.supplier import Supplier

@frappe.whitelist()
def get_customer_ref_code(item_code, customer):
	ref_code = db.get_value("Item Customer Detail", {'parent': item_code, 'customer_name': customer}, 'ref_code')
	return ref_code if ref_code else ''

@frappe.whitelist()
def customer_auto_name(self, method):
	if self.alias and self.customer_name != self.alias:
		self.name = self.alias

@frappe.whitelist()
def customer_override_after_rename(self, method, *args, **kwargs):
	Customer.after_rename = cust_after_rename

def cust_after_rename(self, olddn, newdn, merge=False):
	if frappe.defaults.get_global_default('cust_master_name') == 'Customer Name' and self.alias == self.customer_name:
		frappe.db.set(self, "customer_name", newdn)

@frappe.whitelist()
def supplier_auto_name(self, method):
	if self.alias and self.supplier_name != self.alias:
		self.name = self.alias

@frappe.whitelist()
def supplier_override_after_rename(self, method, *args, **kwargs):
	Supplier.after_rename = supp_after_rename

def supp_after_rename(self, olddn, newdn, merge=False):
	if frappe.defaults.get_global_default('supp_master_name') == 'Supplier Name' and self.alias == self.supplier_name:
		frappe.db.set(self, "supplier_name", newdn)

@frappe.whitelist()
def item_validate(self, method):
	fill_customer_code(self)

def fill_customer_code(self):
	""" Append all the customer codes and insert into "customer_code" field of item table """
	cust_code = []
	for d in self.get('customer_items'):
		cust_code.append(d.ref_code)
	self.customer_code = ""
	self.item_customer_code = ','.join(cust_code)

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

@frappe.whitelist()
def IP_before_save(self,method):
	fetch_item_group(self)

def fetch_item_group(self):
	item_group = frappe.db.get_value("Item", self.item_code, "item_group")
	("item_group", item_group)

@frappe.whitelist()
def upadte_item_price(item, price_list, per_unit_price):
	if db.exists("Item Price",{"item_code":item,"price_list":price_list}):
		name = db.get_value("Item Price",{"item_code":item,"price_list":price_list},'name')
		db.set_value("Item Price",name,"price_list_rate", per_unit_price)
	else:
		item_price = frappe.new_doc("Item Price")
		item_price.price_list = price_list
		item_price.item_code = item
		item_price.price_list_rate = per_unit_price
		
		item_price.save()
	db.commit()
		
	return "Item Price Updated!"

@frappe.whitelist()	
def update_item_price_daily():
	data = db.sql("""
		select 
			item, per_unit_price , buying_price_list
		from
			`tabBOM` 
		where 
			docstatus < 2 
			and is_default = 1 """,as_dict =1)
			
	for row in data:
		upadte_item_price(row.item, row.buying_price_list, row.per_unit_price)
		
	return "Latest price updated in Price List."

@frappe.whitelist()
def bom_before_save(self, method):
	cost_calculation(self)

def cost_calculation(self):
	operating_cost = flt(self.volume_quantity) * flt(self.volume_rate)
	self.total_cost = self.raw_material_cost + self.total_operational_cost + operating_cost - self.scrap_material_cost 
	per_unit_price = flt(self.total_cost) / flt(self.quantity)
	self.spray_drying_cost = operating_cost

	if self.per_unit_price != per_unit_price:
		self.per_unit_price  = per_unit_price
		

@frappe.whitelist()
def enqueue_update_cost():
	frappe.enqueue("chemical.api.update_cost")
	frappe.msgprint(_("Queued for updating latest price in all Bill of Materials. It may take a few minutes."))

def update_cost():
	from erpnext.manufacturing.doctype.bom.bom import get_boms_in_bottom_up_order

	bom_list = get_boms_in_bottom_up_order()
	for bom in bom_list:
		bom_obj = frappe.get_doc("BOM", bom)
		bom_obj.update_cost(update_parent=False, from_child_bom=True)

		per_unit_price = flt(bom_obj.total_cost) / flt(bom_obj.quantity)

		if bom_obj.per_unit_price != per_unit_price:
			bom_obj.db_set('per_unit_price', per_unit_price)		

@frappe.whitelist()
def override_po_functions(self, method):
	WorkOrder.get_status = get_status
	WorkOrder.update_work_order_qty = update_work_order_qty

def get_status(self, status=None):

	'''Return the status based on stock entries against this Work Order'''
	if not status:
		status = self.status

	if self.docstatus==0:
		status = 'Draft'
	elif self.docstatus==1:
		if status != 'Stopped':
			stock_entries = frappe._dict(frappe.db.sql("""select purpose, sum(fg_completed_qty)
				from `tabStock Entry` where work_order=%s and docstatus=1
				group by purpose""", self.name))

			status = "Not Started"
			if stock_entries:
				status = "In Process"
				produced_qty = stock_entries.get("Manufacture")

				under_production = flt(frappe.db.get_value("Manufacturing Settings", None, "under_production_allowance_percentage"))
				allowed_qty = flt(self.qty) * (100 - under_production) / 100.0

				if flt(produced_qty) >= flt(allowed_qty):
					status = "Completed"
	else:
		status = 'Cancelled'

	return status

def update_work_order_qty(self):
	"""Update **Manufactured Qty** and **Material Transferred for Qty** in Work Order
		based on Stock Entry"""

	for purpose, fieldname in (("Manufacture", "produced_qty"),
		("Material Transfer for Manufacture", "material_transferred_for_manufacturing")):
		qty = flt(frappe.db.sql("""select sum(fg_completed_qty)
			from `tabStock Entry` where work_order=%s and docstatus=1
			and purpose=%s""", (self.name, purpose))[0][0])

		self.db_set(fieldname, qty)

@frappe.whitelist()
def stock_entry_before_save(self, method):
	get_based_on(self)
	cal_target_yield_cons(self)
	if self.purpose == 'Repack' and cint(self.from_ball_mill) != 1:
		self.get_stock_and_rate()

def get_based_on(self):
	if self.work_order:
		self.based_on = frappe.db.get_value("Work Order", self.work_order, 'based_on')

def cal_target_yield_cons(self):
	cal_yield = 0
	cons = 0
	tot_quan = 0
	item_arr = list()
	item_map = dict()

	if self.purpose == "Manufacture":
		for d in self.items:
			if d.item_code not in item_arr:
				item_map.setdefault(d.item_code, 0)
			
			item_map[d.item_code] += flt(d.qty)

		# Last row object
		last_row = self.items[-1]

		# Last row batch_yield
		batch_yield = last_row.batch_yield

		# List of item_code from items table
		items_list = [row.item_code for row in self.items]

		# Check if items list has "Vinyl Sulphone (V.S)" and no based_on value
		if not self.based_on and "Vinyl Sulphone (V.S)" in items_list:
			cal_yield = flt(last_row.qty / item_map["Vinyl Sulphone (V.S)"]) # Last row qty / sum of items of "Vinyl Sulphone (V.S)" from map variable

		# Check if items list has frm.doc.based_on value
		elif self.based_on in items_list:
			cal_yield = flt(last_row.qty / item_map[self.based_on]) # Last row qty / sum of items of based_on item from map variable

		# if self.bom_no:
		# 	bom_batch_yield = flt(frappe.db.get_value("BOM", self.bom_no, 'batch_yield'))
		# 	cons = flt(bom_batch_yield * 100) / flt(cal_yield)
		# 	last_row.concentration = cons

		last_row.batch_yield = flt(cal_yield) * (flt(last_row.concentration) / 100.0)

@frappe.whitelist()
def stock_entry_on_submit(self, method):
	update_po(self)

def update_po(self):
	if self.purpose in ["Material Transfer for Manufacture", "Manufacture"] and self.work_order:
		if self.purpose == 'Manufacture':
			po = frappe.get_doc("Work Order",self.work_order)
			if self.volume:
				update_po_volume(self, po)
			
			update_po_transfer_qty(self, po)
			update_po_items(self, po)

			last_item = self.items[-1]

			po.batch_yield = last_item.batch_yield
			po.concentration = last_item.concentration
			po.batch = last_item.get('batch_no')
			po.lot_no = last_item.lot_no
			po.valuation_rate = last_item.valuation_rate

			po.save()
			frappe.db.commit()

def update_po_volume(self, po, ignore_permissions = True):
	if not self.volume:
		frappe.throw(_("Please add volume before submitting the stock entry"))

	if self._action == 'submit':
		po.volume += self.volume
		self.volume_cost = flt(flt(self.volume) * flt(self.volume_rate))		
		po.volume_cost +=  self.volume_cost
		#self.save(ignore_permissions = True)
		po.save(ignore_permissions = True)

	elif self._action == 'cancel':
		po.volume -= self.volume
		po.volume_cost -= self.volume_cost
		po.save(ignore_permissions=True)
		
def update_po_transfer_qty(self, po):
	for d in po.required_items:
		se_items_date = frappe.db.sql('''select sum(qty), valuation_rate
			from `tabStock Entry` entry, `tabStock Entry Detail` detail
			where
				entry.work_order = %s
				and entry.purpose = "Manufacture"
				and entry.docstatus = 1
				and detail.parent = entry.name
				and detail.item_code = %s''', (po.name, d.item_code))[0]

		d.db_set('transferred_qty', flt(se_items_date[0]), update_modified = False)
		d.db_set('valuation_rate', flt(se_items_date[1]), update_modified = False)

def update_po_items(self,po):
	from erpnext.stock.utils import get_latest_stock_qty

	for row in self.items:
		if row.s_warehouse and not row.t_warehouse:
			item = [d.name for d in po.required_items if d.item_code == row.item_code]

			if not item:
				po.append('required_items', {
					'item_code': row.item_code,
					'item_name': row.item_name,
					'description': row.description,
					'source_warehouse': row.s_warehouse,
					'required_qty': row.qty,
					'transferred_qty': row.qty,
					'valuation_rate': row.valuation_rate,
					'available_qty_at_source_warehouse': get_latest_stock_qty(row.item_code, row.s_warehouse),
				})

	for child in po.required_items:
		child.db_update()

@frappe.whitelist()
def stock_entry_on_cancel(self, method):
	if self.work_order:
		pro_doc = frappe.get_doc("Work Order", self.work_order)
		set_po_status(self, pro_doc)
		if self.volume:		
			update_po_volume(self, pro_doc)
			
		update_po_transfer_qty(self, pro_doc)

		pro_doc.save()
		frappe.db.commit()

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)

@frappe.whitelist()
def dn_on_submit(self, method):
	update_sales_invoice(self)

@frappe.whitelist()
def dn_before_cancel(self, method):
	update_sales_invoice(self)

def update_sales_invoice(self):
	for row in self.items:
		if row.against_sales_invoice and row.si_detail:
			if self._action == 'submit':
				delivery_note = self.name
				dn_detail = row.name

			elif self._action == 'cancel':
				delivery_note = ''
				dn_detail = ''

			frappe.db.sql("""update `tabSales Invoice Item` 
				set dn_detail = %s, delivery_note = %s 
				where name = %s """, (dn_detail, delivery_note, row.si_detail))
