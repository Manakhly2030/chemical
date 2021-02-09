import frappe
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from chemical.api import se_cal_rate_qty, se_repack_cal_rate_qty, cal_actual_valuations
from six import iteritems
from frappe import msgprint, _

def onload(self,method):
	pass
	#quantity_price_to_qty_rate(self)

def before_validate(self,method):
	if self.purpose in ['Material Receipt','Repack'] and hasattr(self,'party_type') and hasattr(self,'reference_docname') and hasattr(self,'jw_ref'):
		if not self.reference_docname and not self.jw_ref and self.party_type == "Supplier":
			se_repack_cal_rate_qty(self)
		else:
			se_cal_rate_qty(self)
	else:
		se_cal_rate_qty(self)
	fg_completed_quantity_to_fg_completed_qty(self)
	cal_actual_valuations(self)
	validate_fg_completed_quantity(self)

def validate(self,method):
	if self.purpose in ['Manufacture']:
		item_list = [item.item_code for item in self.items]
		if self.based_on not in item_list:
			frappe.throw("Based on Item {} Required in Raw Materials".format(frappe.bold(self.based_on)))	
	cal_validate_additional_cost_qty(self)
	update_additional_cost_scrap(self)
	calculate_rate_and_amount(self)
	get_based_on(self)
	cal_target_yield_cons(self)

def stock_entry_validate(self, method):
	if self.purpose == "Material Receipt":
		validate_batch_wise_item_for_concentration(self)
	#update_additional_cost(self)

def stock_entry_before_save(self, method):
	if self.purpose == 'Repack' and cint(self.from_ball_mill) != 1:
		self.get_stock_and_rate()

def before_submit(self, method):
	if self.purpose == "Manufacture" and self.bom_no:
		if frappe.db.get_value("BOM",self.bom_no,"inspection_required")==1:
			for row in self.items:
				if row.t_warehouse and not row.quality_inspection:
					frappe.throw(_("Quality Inspection is mandatory in row {0} for item {1}.".format(row.idx,row.item_code)))
	validate_concentration(self)

def se_before_submit(self, method):
	validate_concentration(self)

def stock_entry_on_submit(self, method):
	update_po(self)

def se_before_cancel(self, method):
	StockEntry.delete_auto_created_batches = delete_auto_created_batches
	if self.work_order:
		wo = frappe.get_doc("Work Order",self.work_order)
		wo.db_set('batch','')

def on_cancel(self,method):	
	update_work_order_on_cancel(self,method)

	for item in self.items:
		if item.t_warehouse:
			item.batch_no = None
			item.db_set("batch_no",None)

	for data in frappe.get_all("Batch",{'reference_name': self.name, 'reference_doctype': self.doctype}):
		frappe.db.set_value('Batch',data.name,'reference_name','')
		frappe.db.set_value('Batch',data.name,'valuation_rate',0)
		#frappe.delete_doc("Batch", data.name)

def stock_entry_on_cancel(self, method):
	if self.work_order:
		pro_doc = frappe.get_doc("Work Order", self.work_order)
		set_po_status(self, pro_doc)			
		update_po_transfer_qty(self, pro_doc)
		#pro_doc.save()
		#frappe.db.commit()

def quantity_price_to_qty_rate(self):
	for item in self.items:
		if item.qty and item.quantity == 0:
			item.db_set("quantity",flt(item.qty))
		if item.basic_rate and item.price ==0:
			item.db_set("price",flt(item.basic_rate))

def validate_fg_completed_quantity(self):
	if self.purpose == "Manufacture" and self.work_order:
		#production_item = frappe.get_value('Work Order', self.work_order, 'production_item')
		fg_qty = 0.0
		fg_quantity = 0.0	
		for item in self.items:
			if item.t_warehouse:
				fg_qty += item.qty
				fg_quantity += item.quantity
		self.fg_completed_qty = round(fg_qty,3)
		self.fg_completed_quantity = fg_quantity
		# if fg_quantity != self.fg_completed_quantity:
		# 	frappe.throw(_("Finished product quantity <b>{0}</b> and For Quantity <b>{1}</b> cannot be different")
		# 			.format(fg_quantity, self.fg_completed_quantity))	
	
def get_based_on(self):
	if self.work_order:
		self.based_on = frappe.db.get_value("Work Order", self.work_order, 'based_on')


def	update_additional_cost_scrap(self):
	if self.purpose == "Manufacture" and self.bom_no:
		bom_qty = 1
		se_qty = 1
		bom = frappe.get_doc("BOM",self.bom_no)
		for m in self.items:
			if m.item_code == bom.based_on:
				se_qty = m.qty
				break

		for row in bom.items:
			if row.item_code == bom.based_on:
				bom_qty = row.qty
				break

		amount = 0
		if bom.scrap_items:
			if self.is_new() and not self.amended_from:
				for d in bom.scrap_items:
					self.append('additional_costs', {
						'description': d.item_code,
						'qty': flt(flt(se_qty * d.stock_qty)/ bom_qty),
						'rate': abs(d.rate),
						'amount':  abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ bom_qty)
					})
			else:
				for d in bom.scrap_items:
					for i in self.additional_costs:
						if i.description == d.item_code:
							i.qty = flt(flt(se_qty * d.stock_qty)/ row.qty)
							i.rate = abs(d.rate)
							i.amount = abs(d.rate)* flt(flt(se_qty * d.stock_qty)/ row.qty)    
							break

def sum_total_additional_costs(self):
	self.total_additional_costs = sum(m.amount for m in self.additional_costs)

def calculate_rate_and_amount(self,force=False,update_finished_item_rate=True, raise_error_if_no_rate=True):
	if self.purpose in ['Manufacture','Repack']:
		is_multiple_finish  = 0
		for d in self.items:
			if d.t_warehouse and d.qty != 0:
				is_multiple_finish +=1
		if is_multiple_finish > 1 and self.purpose == "Manufacture":
			self.set_basic_rate(force, update_finished_item_rate=False, raise_error_if_no_rate=True)
			bom_doc = frappe.get_doc("BOM",self.bom_no)
			if hasattr(bom_doc,'equal_cost_ratio'):
				if not bom_doc.equal_cost_ratio:
					cal_rate_for_finished_item(self)
				else:
					calculate_multiple_repack_valuation(self)
			else:
				cal_rate_for_finished_item(self)

		elif is_multiple_finish > 1 and self.purpose == "Repack":
			self.set_basic_rate(force, update_finished_item_rate=False, raise_error_if_no_rate=True)
			calculate_multiple_repack_valuation(self)
		
		else:
			self.set_basic_rate(force, update_finished_item_rate=True, raise_error_if_no_rate=True)
			self.distribute_additional_costs()

	else:
		self.set_basic_rate(force, update_finished_item_rate=True, raise_error_if_no_rate=True)
		self.distribute_additional_costs()

	self.update_valuation_rate()
	# Finbyz Changes start: Calculate Valuation Price Based on Valuation Rate and concentration for AS IS Items 
	update_valuation_price(self)
	# Finbyz Changes End
	self.set_total_incoming_outgoing_value()
	self.set_total_amount()
	price_to_rate(self)

def price_to_rate(self):
	for item in self.items:
		has_batch_no,maintain_as_is_stock = frappe.db.get_value('Item', item.item_code, ['has_batch_no','maintain_as_is_stock'])
		concentration = item.concentration or 100	
		if item.basic_rate:
			if maintain_as_is_stock:
				item.price = flt(item.basic_rate)*100/concentration
			else:
				item.price = flt(item.basic_rate)	
def cal_target_yield_cons(self):
	cal_yield = 0
	cons = 0
	tot_quan = 0
	item_arr = list()
	item_map = dict()
	flag = 0
	if self.purpose == "Manufacture" and self.based_on:
		for d in self.items:
			if d.t_warehouse:
				flag+=1		
			
			if d.item_code not in item_arr:
					item_map.setdefault(d.item_code, {'quantity':0, 'qty':0, 'yield_weights':0})
				
			item_map[d.item_code]['quantity'] += flt(d.quantity)
			item_map[d.item_code]['qty'] += flt(d.qty)
			item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)

		if flag == 1:
			# Last row object
			last_row = self.items[-1]

			# Last row batch_yield
			batch_yield = last_row.batch_yield

			# List of item_code from items table
			items_list = [row.item_code for row in self.items]

			# Check if items list has frm.doc.based_on value
			if self.based_on in items_list:
				# item_yield = 0.0
				# if item_map[self.based_on]['yield_weights'] > 0:
				# 	item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

				# 	if item_yield:
				# 		cal_yield = flt(item_yield) * flt(last_row.qty / item_map[self.based_on]['quantity']) # Last row qty / sum of items of based_on item from map variable
				# 	else:
				cal_yield =  flt(last_row.qty / item_map[self.based_on]['quantity'])
			last_row.batch_yield = flt(cal_yield) * (flt(last_row.concentration) / 100.0)		

def cal_validate_additional_cost_qty(self):
	if self.additional_costs:
		for addi_cost in self.additional_costs:
			addi_cost.amount = flt(addi_cost.qty) * flt(addi_cost.rate)
			if addi_cost.uom == "FG QTY":
				addi_cost.qty = self.fg_completed_quantity
				addi_cost.amount = flt(self.fg_completed_quantity) * flt(addi_cost.rate)

def fg_completed_quantity_to_fg_completed_qty(self):
	if self.fg_completed_qty == 0:
		self.fg_completed_qty = self.fg_completed_quantity
	
def validate_concentration(self):
	if self.work_order and self.purpose == "Manufacture":
		wo_item = frappe.db.get_value("Work Order",self.work_order,'production_item')
		for row in self.items:
			if row.t_warehouse and row.item_code == wo_item and not row.concentration:
				frappe.throw(_("Add concentration in row {} for item {}".format(row.idx,row.item_code)))

def update_po(self):
	if self.work_order:
		po = frappe.get_doc("Work Order", self.work_order)
		if self.purpose == "Material Transfer for Manufacture":
			if po.material_transferred_for_manufacturing > po.qty:
				po.material_transferred_for_manufacturing = po.qty
			
			# if not frappe.db.exists({"doctype":"Stock Entry","name":("!=",self.name),"stock_entry_type":"Material Transfer for Manufacture","work_order":self.work_order}):
			if not frappe.db.sql("""select name from `tabStock Entry` where name != '{}' and stock_entry_type = 'Material Transfer for Manufacture' and work_order = '{}'""".format(self.name,self.work_order)):
				po.db_set('actual_start_date',self.posting_date + ' ' +  self.posting_time)

		if self.purpose == "Manufacture" and self.work_order:
			update_po_transfer_qty(self, po)
			update_po_items(self, po)

			# update finised item detail
			count = 0
			batch_yield = 0.0
			concentration = 0.0
			total_qty = 0.0
			actual_total_qty = 0.0
			valuation_rate = 0.0
			lot = []
			finished_item = {}
			finished_item_list = []
			s = ', '
			
			po.finish_item = []
			if po.bom_no:
				bom_doc = frappe.get_doc("BOM",po.bom_no)
			# po.append("finish_item",finished_item_list)							
			for row in self.items:
				if row.t_warehouse:
					count += 1
					batch_yield += row.batch_yield
					concentration += row.concentration
					total_qty += row.qty
					actual_total_qty += row.quantity
					valuation_rate += flt(row.qty)*flt(row.valuation_rate)
					lot.append(row.lot_no)
					if bom_doc.multiple_finish_item:
						for bom_fi in bom_doc.multiple_finish_item:
							po.append("finish_item",{
								'item_code': row.item_code,
								'actual_qty': row.qty,
								'actual_valuation': row.valuation_rate,
								'lot_no': row.lot_no,
								'purity': row.concentration,
								'packing_size': row.packing_size,
								'no_of_packages': row.no_of_packages,
								'batch_yield': row.batch_yield,
								'batch_no': row.batch_no,
								"bom_cost_ratio":bom_fi.cost_ratio,
								"bom_qty_ratio":bom_fi.qty_ratio,
								"bom_qty":po.qty * bom_fi.qty_ratio / 100,
								"bom_yield":bom_fi.batch_yield
							})
					else:
						po.append("finish_item",{
							'item_code': row.item_code,
							'actual_qty': row.qty,
							'actual_valuation': row.valuation_rate,
							'lot_no': row.lot_no,
							'purity': row.concentration,
							'packing_size': row.packing_size,
							'no_of_packages': row.no_of_packages,
							'batch_yield': row.batch_yield,
							'batch_no': row.batch_no,
							"bom_cost_ratio":100,
							"bom_qty_ratio":100,
							"bom_qty": po.qty,
							"bom_yield": bom_doc.batch_yield
						})
					# for finish_items in po.finish_item:
					# 	if row.item_code == finish_items.item_code:
					# 		finish_items.db_set("item_code",row.item_code)
					# 		finish_items.db_set("actual_qty",row.qty)
					# 		finish_items.db_set("actual_valuation",row.actual_valuation_rate)
					# 		finish_items.db_set("lot_no",row.lot_no)
					# 		finish_items.db_set("packing_size",row.packing_size)
					# 		finish_items.db_set("no_of_packages",row.no_of_packages)
					# 		finish_items.db_set("purity",row.concentration)
					# 		finish_items.db_set("batch_yield",row.batch_yield)
					# 		finish_items.db_set("batch_no",row.batch_no)
					# 		actual_valuation += (flt(row.qty) * row.actual_valuation_rate)
			
			for child in po.finish_item:
				child.db_update()
			po.db_set("batch_yield", flt(batch_yield/count))
			po.db_set("concentration", flt(concentration/count))
			po.db_set("valuation_rate", valuation_rate / flt(actual_total_qty))
			po.db_set("produced_qty", total_qty)
			po.db_set("produced_quantity",actual_total_qty)
			# valuation price = valuation_rate * produced_qty / produced_quantity
			po.db_set('valuation_price',(((flt(valuation_rate) / flt(actual_total_qty)) * total_qty) / actual_total_qty))
			if len(lot)!=0:
				po.db_set("lot_no", s.join(lot))

def update_work_order_on_cancel(self, method):
	if self.purpose == 'Manufacture' and self.work_order:
		doc = frappe.get_doc("Work Order",self.work_order)
		# doc.finish_item = []
		# doc.db_set('batch_yield',0)
		# doc.db_set('concentration',0)
		# doc.db_set('valuation_rate',0)
		# doc.db_set('produced_quantity',0)
		# doc.db_set('lot_no','')
		for item in doc.finish_item:
			item.db_set("actual_qty",0)
			item.db_set("actual_valuation",0)
			item.db_set("lot_no",'')
			item.db_set("packing_size",0)
			item.db_set("no_of_packages",0)
			item.db_set("purity",0)
			item.db_set("batch_yield",0)
			item.db_set("batch_no",'')
			# item.db_update()
		# frappe.db.set_value("Work Order",self.work_order,"batch_yield", 0)
		# frappe.db.set_value("Work Order",self.work_order,"concentration",0)
		# frappe.db.set_value("Work Order",self.work_order,"valuation_rate", 0)
		# frappe.db.set_value("Work Order",self.work_order,"produced_quantity", 0)
		# frappe.db.set_value("Work Order",self.work_order,"lot_no", "")

		# frappe.db.sql("""delete from `tabWork Order Finish Item`
		# 	where parent = %s""", self.work_order)
		
		# doc.db_update()

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)

def calculate_multiple_repack_valuation(self):
	self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])
	if self.items:
		qty = 0.0
		quantity = 0.0
		total_outgoing_value = 0.0
		for row in self.items:
			if row.s_warehouse:
				total_outgoing_value += flt(row.basic_amount)
			if row.t_warehouse:
				qty += row.qty
				quantity += row.quantity
		for row in self.items:
			if row.t_warehouse:
				row.basic_amount = flt(total_outgoing_value) * flt(row.quantity)/ quantity
				row.additional_cost = flt(self.total_additional_costs) * flt(row.quantity)/ quantity
				row.basic_rate =  flt(row.basic_amount/ row.qty)

def cal_rate_for_finished_item(self):

	self.total_additional_costs = sum([flt(t.amount) for t in self.get("additional_costs")])
	work_order = frappe.get_doc("Work Order",self.work_order)
	is_multiple_finish = 0
	for d in self.items:
		if d.t_warehouse:
			is_multiple_finish +=1
	if is_multiple_finish > 1:
		total_incoming_amount = 0.0
		item_arr = list()
		item_map = dict()
		finished_list = []
		result = {}
		cal_yield = 0
		if self.purpose == 'Manufacture' and self.bom_no:
			for row in self.items:
				if row.t_warehouse:
					finished_list.append({row.item_code:row.quantity}) #create a list of dict of finished item
			for d in finished_list:
				for k in d.keys():
					result[k] = result.get(k, 0) + d[k] # create a dict of unique item 
						
			for d in self.items:
				if d.item_code not in item_arr:
					item_map.setdefault(d.item_code, {'quantity':0, 'qty':0, 'yield_weights':0})
				
				item_map[d.item_code]['quantity'] += flt(d.quantity)
				item_map[d.item_code]['qty'] += flt(d.qty)
				item_map[d.item_code]['yield_weights'] += flt(d.batch_yield)*flt(d.quantity)

				
				if d.t_warehouse:
					for finish_items in work_order.finish_item:
						if d.item_code == finish_items.item_code:
							d.db_set('basic_amount',flt(flt(self.total_outgoing_value*finish_items.bom_cost_ratio*d.quantity)/flt(100*result[d.item_code])))
							d.db_set('additional_cost',flt(flt(self.total_additional_costs*finish_items.bom_cost_ratio*d.quantity)/flt(100*result[d.item_code])))
							d.db_set('amount',flt(d.basic_amount + d.additional_cost))
							d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
							d.db_set('valuation_rate',flt(d.amount/ d.qty))
							print(result[d.item_code])
							print(finish_items.bom_cost_ratio)
							item_yield = 0.0
							if item_map[self.based_on]['yield_weights'] > 0:
								item_yield = item_map[self.based_on]['yield_weights'] / item_map[self.based_on]['quantity']

							based_on_qty_ratio = d.quantity / (self.fg_completed_quantity or self.fg_completed_qty)
							if self.based_on:
								# if item_yield:
								# 	d.batch_yield = flt((d.qty * d.concentration * item_yield) / (100*flt(item_map[self.based_on]['quantity']*finish_items.bom_qty_ratio/100)))
								# else:
								d.batch_yield = flt((d.qty * d.concentration) / (100*flt(item_map[self.based_on]['quantity']*flt(based_on_qty_ratio)/100)))

						total_incoming_amount += flt(d.amount)

			d.db_update()

					# first_item_ratio = abs(100-self.cost_ratio_of_second_item)
					# first_item_qty_ratio = abs(100-self.qty_ratio_of_second_item)
					
					# if d.item_code == frappe.db.get_value('Work Order',self.work_order,'production_item'):
					# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
					# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*first_item_ratio*d.quantity)/flt(100*result[d.item_code])))
					# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
					# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
					# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))

					# 	if self.based_on:
					# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*first_item_qty_ratio/100))
						
					# if d.item_code == self.second_item:
					# 	d.db_set('basic_amount',flt(flt(self.total_outgoing_value*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
					# 	d.db_set('additional_cost',flt(flt(self.total_additional_costs*self.cost_ratio_of_second_item*d.quantity)/flt(100*result[d.item_code])))
					# 	d.db_set('amount',flt(d.basic_amount + d.additional_cost))
					# 	d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
					# 	d.db_set('valuation_rate',flt(d.amount/ d.qty))
						
					# 	if self.based_on:
					# 		d.batch_yield = flt(result[d.item_code] / flt(item_map[self.based_on]*self.qty_ratio_of_second_item/100))  # cost_ratio_of_second_item percent of sum of items of based_on item from map variable 				

def update_valuation_price(self):
	for item in self.items:
		maintain_as_is_stock = frappe.db.get_value('Item', item.item_code, 'maintain_as_is_stock')
		concentration = item.concentration or 100
		if maintain_as_is_stock:
			item.valuation_price = item.valuation_rate * 100 / concentration
		else:
			item.valuation_price = item.valuation_rate

def update_additional_cost(self):
	if self.purpose == "Manufacture" and self.bom_no:
		bom = frappe.get_doc("BOM",self.bom_no)
		abbr = frappe.db.get_value("Company",self.company,'abbr')
		
		if self.is_new() and not self.amended_from:
			if bom.additional_cost:
				for d in bom.additional_cost:
					self.append('additional_costs', {
						'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
						'description': d.description,
						'qty': flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity),
						'rate': abs(d.rate),
						'amount':  abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
					})
		else:
			for row in self.additional_costs:
				if bom.additional_cost:
					for d in bom.additional_cost:
						if row.description == d.description:
							row.rate = abs(d.rate)
							row.qty = flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
							row.amount = abs(d.rate)* flt(flt(self.fg_completed_quantity * bom.quantity)/ bom.quantity)
		self.db_set('total_additional_costs',sum([row.amount for row in self.additional_costs]))

def validate_lot(self):
	for row in self.items:
		if row.t_warehouse and not row.s_warehouse:
			if not row.lot_no:
				frappe.throw(_("Add lot_no in row {} for item {}".format(row.idx,row.item_code)))
	
def validate_batch_wise_item_for_concentration(self):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		# if not has_batch_no and flt(row.concentration):
			# frappe.throw(_("Row #{idx}. Please remove concentration for non batch item {item_code}.".format(idx = row.idx, item_code = frappe.bold(row.item_code))))
		if not has_batch_no:
			row.concentration = 100


def update_po_volume(self, po, ignore_permissions = True):
	# if not self.volume:
	# 	frappe.throw(_("Please add volume before submitting the stock entry"))

	if self._action == 'submit':
		# po.volume += self.volume
		# self.volume_cost = flt(flt(self.volume) * flt(self.volume_rate))		
		# po.volume_cost +=  self.volume_cost
		#self.save(ignore_permissions = True)
		po.save(ignore_permissions = True)

	elif self._action == 'cancel':
		# po.volume -= self.volume
		# po.volume_cost -= self.volume_cost
		po.db_set('batch','')
		po.save(ignore_permissions=True)
		
def update_po_transfer_qty(self, po):
	for d in po.required_items:
		se_items_date = frappe.db.sql('''select sum(quantity), valuation_rate
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
					'transferred_qty': row.quantity,
					'valuation_rate': row.valuation_rate,
					'available_qty_at_source_warehouse': get_latest_stock_qty(row.item_code, row.s_warehouse),
				})

	for child in po.required_items:
		child.db_update()

def validate_finished_goods(self):
	"""validation: finished good quantity should be same as manufacturing quantity"""
	if not self.work_order: return

	items_with_target_warehouse = []
	allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
		"overproduction_percentage_for_work_order"))

	production_item, wo_qty = frappe.db.get_value("Work Order",
		self.work_order, ["production_item", "qty"])

	for d in self.get('items'):
		if (self.purpose != "Send to Subcontractor" and d.bom_no
			and flt(round(d.transfer_qty,3)) > flt(round(self.fg_completed_qty,3)) and d.item_code == production_item):
			frappe.throw(_("Quantity in row {0} ({1}) must be same as manufactured quantity {2}"). \
				format(d.idx, round(d.transfer_qty,3), round(self.fg_completed_qty,3)))

		if self.work_order and self.purpose == "Manufacture" and d.t_warehouse:
			items_with_target_warehouse.append(d.item_code)

	if self.work_order and self.purpose == "Manufacture":
		allowed_qty = wo_qty + (allowance_percentage/100 * wo_qty)
		#Finbyz Changes: self.fg_completed_qty to self.if self.fg_completed_quantity
		if self.fg_completed_quantity > allowed_qty:
			frappe.throw(_("For quantity {0} should not be grater than work order quantity {1}")
				.format(flt(self.fg_completed_quantity), wo_qty))

		if production_item not in items_with_target_warehouse:
			frappe.throw(_("Finished Item {0} must be entered for Manufacture type entry")
				.format(production_item))

def delete_auto_created_batches(self):
	pass


