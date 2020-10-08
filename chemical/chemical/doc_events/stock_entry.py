import frappe
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from chemical.api import se_cal_rate_qty, cal_actual_valuations
from six import iteritems
from frappe import msgprint, _

def onload(self,method):
	quantity_price_to_qty_rate(self)

def before_validate(self,method):
	se_cal_rate_qty(self)
	fg_completed_quantity_to_fg_completed_qty(self)
	cal_actual_valuations(self)
	validate_fg_completed_quantity(self)

def validate(self,method):
	calculate_rate_and_amount(self)
	cal_target_yield_cons(self)
	cal_validate_additional_cost_qty
	get_based_on(self)
	#update_additional_cost(self)
	update_additional_cost_scrap(self)
	
def stock_entry_validate(self, method):
	if self.purpose == "Material Receipt":
		validate_batch_wise_item_for_concentration(self)
	#update_additional_cost(self)

def stock_entry_before_save(self, method):
	get_based_on(self)
	cal_target_yield_cons(self)
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

def on_submit(self, method):
	try:
		update_po(self)
	except Exception as e:
		frappe.throw(str(e))

def stock_entry_on_submit(self, method):
	update_po(self)

def se_before_cancel(self, method):
	StockEntry.delete_auto_created_batches = delete_auto_created_batches
	if self.work_order:
		wo = frappe.get_doc("Work Order",self.work_order)
		wo.db_set('batch','')

def on_cancel(self,method):
	try:
		update_work_order_on_cancel(self,method)
	except Exception as e:
		frappe.throw(str(e))
	
	for item in self.items:
		if item.t_warehouse:
			item.batch_no = None
			item.db_set("batch_no",None)

	for data in frappe.get_all("Batch",{'reference_name': self.name, 'reference_doctype': self.doctype}):
		frappe.delete_doc("Batch", data.name)

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
		self.fg_completed_qty = fg_qty
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
	if self.purpose == 'Manufacture' and self.bom_no:
		se_cal_rate_qty(self)
		is_multiple_finish  = 0
		for d in self.items:
			if d.t_warehouse:
				is_multiple_finish +=1
		if is_multiple_finish  > 1:
			self.set_basic_rate(force, update_finished_item_rate=False, raise_error_if_no_rate=True)
			cal_rate_for_finished_item(self)
			self.set_total_incoming_outgoing_value()
			self.set_total_amount()
		else:
			self.set_basic_rate(force, update_finished_item_rate=True, raise_error_if_no_rate=True)
			self.distribute_additional_costs()
			self.update_valuation_rate()
			self.set_total_incoming_outgoing_value()
			self.set_total_amount()
	else:
		self.set_basic_rate(force, update_finished_item_rate=True, raise_error_if_no_rate=True)
		self.distribute_additional_costs()
		self.update_valuation_rate()
		self.set_total_incoming_outgoing_value()
		self.set_total_amount()
					
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
				item_map.setdefault(d.item_code, 0)
			
			item_map[d.item_code] += flt(d.qty)
			
		if flag == 1:
			# Last row object
			last_row = self.items[-1]

			# Last row batch_yield
			batch_yield = last_row.batch_yield

			# List of item_code from items table
			items_list = [row.item_code for row in self.items]

			# Check if items list has frm.doc.based_on value
			if self.based_on in items_list:
				cal_yield = flt(last_row.qty / item_map[self.based_on]) # Last row qty / sum of items of based_on item from map variable

			last_row.batch_yield = flt(cal_yield) * (flt(last_row.concentration) / 100.0)		

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

					for finish_items in po.finish_item:
						if row.item_code == finish_items.item_code:
							finish_items.db_set("item_code",row.item_code)
							finish_items.db_set("actual_qty",row.qty)
							finish_items.db_set("actual_valuation",row.actual_valuation_rate)
							finish_items.db_set("lot_no",row.lot_no)
							finish_items.db_set("packing_size",row.packing_size)
							finish_items.db_set("no_of_packages",row.no_of_packages)
							finish_items.db_set("purity",row.concentration)
							finish_items.db_set("batch_yield",row.batch_yield)
							finish_items.db_set("batch_no",row.batch_no)
					# finished_item['item_code'] = row.item_code
					# finished_item['quantity']  = row.quantity
					# finished_item['actual_valuation'] = row.actual_valuation_rate
					# finished_item['lot_no'] = row.lot_no
					# finished_item['packing_size'] = row.packing_size
					# finished_item['no_of_packages'] = row.no_of_packages
					# finished_item['purity'] = row.concentration
					# finished_item['batch_yield'] = row.batch_yield
					# finished_item['batch_no'] = row.batch_no
					# po.append("finish_item",finished_item)
					# finished_item_list.append(finished_item)
					
			for child in po.finish_item:
				child.db_update()
			po.db_set("batch_yield", flt(batch_yield/count))
			po.db_set("concentration", flt(concentration/count))
			po.db_set("valuation_rate", flt(valuation_rate/total_qty))
			po.db_set("produced_qty", total_qty)
			po.db_set("produced_quantity",actual_total_qty)
			if len(lot)!=0:
				po.db_set("lot_no", s.join(lot))

def update_work_order_on_cancel(self, method):
	if self.purpose == 'Manufacture' and self.work_order:
		frappe.db.set_value("Work Order",self.work_order,"batch_yield", 0)
		frappe.db.set_value("Work Order",self.work_order,"concentration",0)
		frappe.db.set_value("Work Order",self.work_order,"valuation_rate", 0)
		frappe.db.set_value("Work Order",self.work_order,"produced_quantity", 0)
		frappe.db.set_value("Work Order",self.work_order,"lot_no", "")
		# frappe.db.sql("""delete from `tabWork Order Finish Item`
		# 	where parent = %s""", self.work_order)
		frappe.db.commit()

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)

def cal_rate_for_finished_item(self):
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
					item_map.setdefault(d.item_code, 0)
				
				item_map[d.item_code] += flt(d.quantity)
				
				if d.t_warehouse:
					for finish_items in work_order.finish_item:
						if d.item_code == finish_items.item_code:
							d.db_set('basic_amount',flt(flt(self.total_outgoing_value*finish_items.bom_cost_ratio*d.quantity)/flt(100*result[d.item_code])))
							d.db_set('additional_cost',flt(flt(self.total_additional_costs*finish_items.bom_cost_ratio*d.quantity)/flt(100*result[d.item_code])))
							d.db_set('amount',flt(d.basic_amount + d.additional_cost))
							d.db_set('basic_rate',flt(d.basic_amount/ d.qty))
							d.db_set('valuation_rate',flt(d.amount/ d.qty))

							if self.based_on:
								d.batch_yield = flt(d.qty / flt(item_map[self.based_on]*finish_items.bom_qty_ratio/100))
					
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
					'transferred_qty': row.quantity,
					'valuation_rate': row.valuation_rate,
					'available_qty_at_source_warehouse': get_latest_stock_qty(row.item_code, row.s_warehouse),
				})

	for child in po.required_items:
		child.db_update()

def cal_validate_additional_cost_qty(self):
	if self.additional_costs:
		for addi_cost in self.additional_costs:
			if addi_cost.uom == "FG QTY":
				addi_cost.qty = self.fg_completed_quantity
				addi_cost.amount = flt(self.fg_completed_quantity) * flt(addi_cost.rate)


def delete_auto_created_batches(self):
	pass

