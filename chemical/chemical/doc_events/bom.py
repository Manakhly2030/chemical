import frappe
from frappe import msgprint, _
from frappe.utils import flt
from frappe.utils.background_jobs import enqueue

def bom_validate(self, method):
	price_overrides(self)
	qty_calculation(self)
	cost_calculation(self)

def bom_before_save(self, method):
	cost_calculation(self)
	yield_cal(self)

def yield_cal(self):
	cal_yield = 0
	for d in self.items:
		if self.based_on and self.based_on == d.item_code:
			cal_yield = flt(self.quantity) / flt(d.qty)
			if self.is_multiple_item:
				self.second_item_batch_yield = flt(self.second_item_qty) / d.qty
	
	self.batch_yield = cal_yield

def price_overrides(self):
	for row in self.items:
		if row.from_price_list:
			#row.db_set('bom_no','')
			row.bom_no = ''

def qty_calculation(self):
	if self.is_multiple_item:
		self.db_set('quantity',flt(self.total_quantity * self.qty_ratio_of_first_item)/100.0)
		self.db_set('second_item_qty', flt(self.total_quantity - self.quantity))
	
def cost_calculation(self):
	etp_amount = 0
	additional_amount = 0
	self.volume_amount = flt(self.volume_quantity) * flt(self.volume_rate)
	if not self.is_multiple_item:
		self.cost_ratio_of_first_item = 100.0
	
	if hasattr(self, 'etp_qty'):
		etp_amount = flt(self.etp_qty)*flt(self.etp_rate)
		self.etp_amount = flt(self.etp_qty)*flt(self.etp_rate)
		self.db_set('per_unit_etp_cost',(flt(etp_amount/self.quantity) * flt(self.cost_ratio_of_first_item/100.0)))

	for row in self.items:
		row.per_unit_rate = flt(row.amount)/self.quantity * flt(self.cost_ratio_of_first_item/100.0)
	for row in self.scrap_items:
		row.per_unit_rate = flt(row.amount)/self.quantity * flt(self.cost_ratio_of_first_item/100.0)
		
	additional_amount = sum(flt(d.amount) for d in self.additional_cost)
	self.additional_amount = additional_amount
	self.db_set('total_operational_cost',flt(self.additional_amount) + flt(self.volume_amount) + etp_amount)
	self.db_set('total_scrap_cost', abs(self.scrap_material_cost))
	self.db_set('total_cost',self.raw_material_cost + self.total_operational_cost - flt(self.scrap_material_cost))
	per_unit_price = flt(self.total_cost) / flt(self.quantity)
	self.db_set('per_unit_volume_cost',flt(self.volume_amount/self.quantity)* flt(self.cost_ratio_of_first_item/100.0))	
	self.db_set('per_unit_additional_cost',flt(flt(self.additional_amount)/self.quantity)* flt(self.cost_ratio_of_first_item/100.0))
	self.db_set('per_unit_rmc',flt(flt(self.raw_material_cost)/self.quantity)* flt(self.cost_ratio_of_first_item/100.0))
	self.db_set('per_unit_operational_cost',flt(flt(self.total_operational_cost)/self.quantity)* flt(self.cost_ratio_of_first_item/100.0))
	self.db_set('per_unit_scrap_cost',flt(flt(self.total_scrap_cost)/self.quantity) * flt(self.cost_ratio_of_first_item/100.0))

	if self.per_unit_price != per_unit_price:
		self.db_set('per_unit_price', per_unit_price * flt(self.cost_ratio_of_first_item/100.0))
	frappe.db.commit()


# override whitelisted method on hooks
@frappe.whitelist()
def enqueue_update_cost():
	frappe.enqueue("chemical.chemical.doc_events.bom.update_cost")
	frappe.msgprint(_("Queued for updating latest price in all Bill of Materials. It may take a few minutes."))

def update_cost():
	from erpnext.manufacturing.doctype.bom.bom import get_boms_in_bottom_up_order

	bom_list = get_boms_in_bottom_up_order()
	for bom in bom_list:
		bom_obj = frappe.get_doc("BOM", bom)
		bom_obj.update_cost(update_parent=False, from_child_bom=True)
		if not bom_obj.is_multiple_item:
			bom_obj.cost_ratio_of_first_item = 100.0
		for row in bom_obj.items:
			row.db_set('per_unit_rate', flt(row.amount)/bom_obj.quantity * flt(bom_obj.cost_ratio_of_first_item/100.0))
		for row in bom_obj.scrap_items:
			row.db_set('per_unit_rate', flt(row.amount)/bom_obj.quantity * flt(bom_obj.cost_ratio_of_first_item/100.0))
			
		bom_obj.db_set("volume_amount",flt(bom_obj.volume_quantity) * flt(bom_obj.volume_rate))
		bom_obj.db_set("etp_amount",flt(bom_obj.etp_qty) * flt(bom_obj.etp_rate))
		bom_obj.db_set('total_operational_cost',flt(bom_obj.additional_amount) + flt(bom_obj.volume_amount) + flt(bom_obj.etp_amount))
		bom_obj.db_set('total_scrap_cost', abs(bom_obj.scrap_material_cost))
		bom_obj.db_set("total_cost",bom_obj.raw_material_cost + bom_obj.total_operational_cost - flt(bom_obj.scrap_material_cost) )
		per_unit_price = flt(bom_obj.total_cost) / flt(bom_obj.quantity)
		bom_obj.db_set('per_unit_price',flt(bom_obj.total_cost) / flt(bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))
		bom_obj.db_set('per_unit_volume_cost',flt(bom_obj.volume_amount/bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))	
		bom_obj.db_set('per_unit_additional_cost',flt(flt(bom_obj.additional_amount)/bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))
		bom_obj.db_set('per_unit_rmc',flt(flt(bom_obj.raw_material_cost)/bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))
		bom_obj.db_set('per_unit_operational_cost',flt(flt(bom_obj.total_operational_cost)/bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))
		bom_obj.db_set('per_unit_scrap_cost',flt(flt(bom_obj.total_scrap_cost)/bom_obj.quantity) * flt(bom_obj.cost_ratio_of_first_item/100.0))

		# if bom_obj.per_unit_price != per_unit_price:
			# bom_obj.db_set('per_unit_price', per_unit_price)
		if frappe.db.exists("Item Price",{"item_code":bom_obj.item,"price_list":bom_obj.buying_price_list}):
			name = frappe.db.get_value("Item Price",{"item_code":bom_obj.item,"price_list":bom_obj.buying_price_list},'name')
			frappe.db.set_value("Item Price",name,"price_list_rate", per_unit_price)
		else:
			item_price = frappe.new_doc("Item Price")
			item_price.price_list = bom_obj.buying_price_list
			item_price.item_code = bom_obj.item
			item_price.price_list_rate = per_unit_price
			
			item_price.save()
		frappe.db.commit()

# update price in BOM
# call it in bom.js
@frappe.whitelist()
def upadte_item_price(docname,item, price_list, per_unit_price):
	doc = frappe.get_doc("BOM",docname)
	if not doc.is_multiple_item:
		doc.cost_ratio_of_first_item = 100.0
	for row in doc.items:
		row.db_set('per_unit_rate', flt(row.amount)/doc.quantity * flt(doc.cost_ratio_of_first_item/100.0))
	for row in doc.scrap_items:
		row.db_set('per_unit_rate', flt(row.amount)/doc.quantity * flt(doc.cost_ratio_of_first_item/100.0))
	doc.db_set('volume_amount',flt(doc.volume_quantity) * flt(doc.volume_rate))
	doc.db_set('etp_amount',flt(doc.etp_qty) * flt(doc.etp_rate))
	doc.db_set('total_operational_cost',flt(doc.additional_amount) + flt(doc.volume_amount) + flt(doc.etp_amount))
	doc.db_set('total_scrap_cost', abs(doc.scrap_material_cost))
	doc.db_set("total_cost",doc.raw_material_cost + flt(doc.total_operational_cost) - flt(doc.scrap_material_cost))
	doc.db_set('per_unit_price',flt(doc.total_cost) / flt(doc.quantity) * flt(doc.cost_ratio_of_first_item/100.0))
	doc.db_set('per_unit_volume_cost',flt(doc.volume_amount/doc.quantity) * flt(doc.cost_ratio_of_first_item/100.0))	
	doc.db_set('per_unit_additional_cost',flt(flt(doc.additional_amount)/doc.quantity)* flt(doc.cost_ratio_of_first_item/100.0))
	doc.db_set('per_unit_rmc',flt(flt(doc.raw_material_cost)/doc.quantity)* flt(doc.cost_ratio_of_first_item/100.0))
	doc.db_set('per_unit_operational_cost',flt(flt(doc.total_operational_cost)/doc.quantity)* flt(doc.cost_ratio_of_first_item/100.0))
	doc.db_set('per_unit_scrap_cost',flt(flt(doc.total_scrap_cost)/doc.quantity)* flt(doc.cost_ratio_of_first_item/100.0))
	
	if frappe.db.exists("Item Price",{"item_code":item,"price_list":price_list}):
		name = frappe.db.get_value("Item Price",{"item_code":item,"price_list":price_list},'name')
		frappe.db.set_value("Item Price",name,"price_list_rate", per_unit_price)
	else:
		item_price = frappe.new_doc("Item Price")
		item_price.price_list = price_list
		item_price.item_code = item
		item_price.price_list_rate = per_unit_price
		
		item_price.save()
	frappe.db.commit()
		
	return "Item Price Updated!"


# Daily price update on hooks
@frappe.whitelist()	
def update_item_price_daily():
	data = frappe.db.sql("""
		select 
			item, per_unit_price , buying_price_list, name
		from
			`tabBOM` 
		where 
			docstatus < 2 
			and is_default = 1 """,as_dict =1)
			
	for row in data:
		upadte_item_price(row.name,row.item, row.buying_price_list, row.per_unit_price)
		
	return "Latest price updated in Price List."
