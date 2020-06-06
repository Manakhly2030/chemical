import frappe
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder

def before_insert(self, method):
	if not self.name and self.is_opening == "Yes":
		self.naming_series = 'O' + self.naming_series

def stock_entry_validate(self, method):
	if self.volume:
		self.volume_cost = self.volume * self.volume_rate
	if self.purpose == "Material Receipt":
		validate_batch_wise_item_for_concentration(self)

def stock_entry_before_save(self, method):
	get_based_on(self)
	cal_target_yield_cons(self)
	if self.purpose == 'Repack' and cint(self.from_ball_mill) != 1:
		self.get_stock_and_rate()
	update_additional_cost(self)

def se_before_submit(self, method):
	override_wo_functions(self)
	validate_concentration(self)

def stock_entry_on_submit(self, method):
	update_po(self)

def se_before_cancel(self, method):
	if self.work_order:
		wo = frappe.get_doc("Work Order",self.work_order)
		wo.db_set('batch','')
	override_wo_functions(self)

def stock_entry_on_cancel(self, method):
	if self.work_order:
		pro_doc = frappe.get_doc("Work Order", self.work_order)
		set_po_status(self, pro_doc)
		if self.volume:		
			update_po_volume(self, pro_doc)
			
		update_po_transfer_qty(self, pro_doc)

		pro_doc.save()
		frappe.db.commit()


def validate_batch_wise_item_for_concentration(self):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		# if not has_batch_no and flt(row.concentration):
			# frappe.throw(_("Row #{idx}. Please remove concentration for non batch item {item_code}.".format(idx = row.idx, item_code = frappe.bold(row.item_code))))
		if not has_batch_no:
			row.concentration = 100

def set_po_status(self, pro_doc):
	status = None
	if flt(pro_doc.material_transferred_for_instruction):
		status = "In Process"

	if status:
		pro_doc.db_set('status', status)


def get_based_on(self):
	if self.work_order:
		self.based_on = frappe.db.get_value("Work Order", self.work_order, 'based_on')
		
def update_additional_cost(self):
	if self.purpose == "Manufacture" and self.bom_no:
		bom = frappe.get_doc("BOM",self.bom_no)
		abbr = frappe.db.get_value("Company",self.company,'abbr')
		if self.is_new() and not self.amended_from:
			self.append("additional_costs",{
                'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
				'description': "Spray drying cost",
				'qty': self.volume,
				'rate': self.volume_rate,
				'amount': self.volume_cost
			})
			if hasattr(self, 'etp_qty'):
				self.append("additional_costs",{
                    'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
					'description': "ETP cost",
					'qty': self.etp_qty,
					'rate': self.etp_rate,
					'amount': flt(self.etp_qty * self.etp_rate)
				})
			if bom.additional_cost:
				for d in bom.additional_cost:
					self.append('additional_costs', {
                        'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
						'description': d.description,
						'qty': flt(flt(self.fg_completed_qty * bom.quantity)/ bom.quantity),
						'rate': abs(d.rate),
						'amount':  abs(d.rate)* flt(flt(self.fg_completed_qty * bom.quantity)/ bom.quantity)
					})
		else:
			for row in self.additional_costs:
				if row.description == "Spray drying cost":
					row.qty = self.volume
					row.rate = self.volume_rate
					row.amount = self.volume_cost
				elif hasattr(self, 'etp_qty') and row.description == "ETP cost":
					row.qty = flt(self.etp_qty)
					row.rate = flt(self.etp_rate)
					row.amount = flt(self.etp_qty) * flt(self.etp_rate)
				elif bom.additional_cost:
					for d in bom.additional_cost:
						if row.description == d.description:
							row.rate = abs(d.rate)
							row.qty = flt(flt(self.fg_completed_qty * bom.quantity)/ bom.quantity)
							row.amount = abs(d.rate)* flt(flt(self.fg_completed_qty * bom.quantity)/ bom.quantity)

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

def validate_concentration(self):
	if self.work_order and self.purpose == "Manufacture":
		wo_item = frappe.db.get_value("Work Order",self.work_order,'production_item')
		for row in self.items:
			if row.t_warehouse and row.item_code == wo_item and not row.concentration:
				frappe.throw(_("Add concentration in row {} for item {}".format(row.idx,row.item_code)))		

def override_wo_functions(self):
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

		if not self.skip_transfer:
			if purpose == "Material Transfer for Manufacture" and self.material_transferred_for_manufacturing > self.qty:
				qty = self.qty

		self.db_set(fieldname, qty)


def update_po(self):
	if self.purpose in ["Material Transfer for Manufacture", "Manufacture"] and self.work_order:
		po = frappe.get_doc("Work Order",self.work_order)
		if self.purpose == "Material Transfer for Manufacture":
			if po.material_transferred_for_manufacturing > po.qty:
				 po.material_transferred_for_manufacturing = po.qty
							
		if self.purpose == 'Manufacture':	
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
