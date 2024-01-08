import frappe
from frappe import _
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details

# Override Production Plan Functions
@frappe.whitelist()
def override_proplan_functions():
	
	ProductionPlan.get_open_sales_orders = get_open_sales_orders
	ProductionPlan.get_items = get_items_from_sample

def get_sales_orders(self):
	so_filter = item_filter = ""
	if self.from_date:
		so_filter += " and so.transaction_date >= %(from_date)s"
	if self.to_date:
		so_filter += " and so.transaction_date <= %(to_date)s"
	if self.customer:
		so_filter += " and so.customer = %(customer)s"
	if self.project:
		so_filter += " and so.project = %(project)s"

	if self.item_code:
		item_filter += " and so_item.item_code = %(item)s"

	open_so = frappe.db.sql("""
		select distinct so.name, so.transaction_date, so.customer, so.base_grand_total
		from `tabSales Order` so, `tabSales Order Item` so_item
		where so_item.parent = so.name
			and so.docstatus = 1 and so.status not in ("Stopped", "Closed","Completed")
			and so.company = %(company)s
			and so_item.qty > so_item.work_order_qty {0} {1}

		""".format(so_filter, item_filter), {
			"from_date": self.from_date,
			"to_date": self.to_date,
			"customer": self.customer,
			"project": self.project,
			"item": self.item_code,
			"company": self.company

		}, as_dict=1)

	return open_so
@frappe.whitelist()
def get_open_sales_orders(self):
		""" Pull sales orders  which are pending to deliver based on criteria selected"""
		open_so = get_sales_orders(self)
		if open_so:
			self.add_so_in_table(open_so)
		else:
			frappe.msgprint(_("Sales orders are not available for production"))

@frappe.whitelist()
def get_items_from_sample(self):
	if self.get_items_from == "Sales Order":
			get_so_items(self)
	elif self.get_items_from == "Material Request":
			self.get_mr_items()

def get_so_items(self):
		so_list = [d.sales_order for d in self.get("sales_orders", []) if d.sales_order]
		if not so_list:
			frappe.msgprint(_("Please enter Sales Orders in the above table"))
			return []
		item_condition = ""
		if self.item_code:
			item_condition = ' and so_item.item_code = "{0}"'.format(frappe.db.escape(self.item_code))
	# -----------------------	custom added code  ------------#

		if self.as_per_projected_qty == 1:                                                           #condition 1
			sample_list = [[d.outward_sample, d.quantity ,d.projected_qty] for d in self.get("finish_items", []) if d.outward_sample]	
			if not sample_list:
				frappe.msgprint(_("Please Get Finished Items."))
				return []	
			item_details = frappe._dict()

			for sample, quantity ,projected_qty in sample_list:#changes here
				if projected_qty < 0:
					sample_doc = frappe.get_doc("Outward Sample",sample)
					for row in sample_doc.details:
						bom_no = frappe.db.exists("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
						
						if bom_no:
							bom = frappe.get_doc("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
							item_details.setdefault(row.item_code, frappe._dict({
								'planned_qty': 0.0,
								'bom_no': bom.name,
								'item_code': row.item_code,
								'concentration' : bom.concentration
							}))
							
							item_details[row.item_code].planned_qty += (flt(abs(projected_qty)) * flt(row.quantity) * flt(row.concentration))/ (flt(sample_doc.total_qty) * flt(bom.concentration) )
			
			items = [values for values in item_details.values()]

		elif self.as_per_actual_qty == 1:															 #condition 2
			
			sample_list = [[d.outward_sample, d.quantity,d.actual_qty] for d in self.get("finish_items", []) if d.outward_sample]	
			if not sample_list:
				frappe.msgprint(_("Please Get Finished Items."))
				return []	
			item_details = frappe._dict()
			for sample, quantity, actual_qty in sample_list:
				diff = actual_qty - quantity #changes here
				if diff < 0:
					sample_doc = frappe.get_doc("Outward Sample",sample)

					for row in sample_doc.details:
						bom_no = frappe.db.exists("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
						if bom_no:
							bom = frappe.get_doc("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
							item_details.setdefault(row.item_code, frappe._dict({
								'planned_qty': 0.0,
								'bom_no': bom.name,
								'item_code': row.item_code,
								'concentration' : bom.concentration
							}))
							
							item_details[row.item_code].planned_qty += (flt(abs(diff)) * flt(row.quantity) * flt(row.concentration)) / (flt(sample_doc.total_qty) * flt(bom.concentration))
							
			items = [values for values in item_details.values()]

		else:		
			 #default
			if self.get_item_based_on_samples == 1:
				sample_list = [[d.outward_sample, d.quantity] for d in self.get("finish_items", []) if d.outward_sample]	
				if not sample_list:
					frappe.msgprint(_("Please Get Finished Items."))
					return []	
				item_details = frappe._dict()
				for sample, quantity in sample_list:
					sample_doc = frappe.get_doc("Outward Sample",sample)

					for row in sample_doc.details:
						bom_no = frappe.db.exists("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
						if bom_no:
							bom = frappe.get_doc("BOM", {'item':row.item_code,'is_active':1,'is_default':1,'docstatus':1})
							# frappe.msgprint(str(bom.name))
						
							item_details.setdefault(row.item_code, frappe._dict({
								'planned_qty': 0.0,
								'bom_no': bom.name,
								'item_code': row.item_code,
								'concentration' : bom.concentration
							}))
							
							item_details[row.item_code].planned_qty += (flt(quantity) * flt(row.quantity) * (row.concentration))/ (flt(sample_doc.total_qty)* (bom.concentration))

				items = [values for values in item_details.values()]
			
	# -----------------------	
		# items = frappe.db.sql("""select distinct parent, item_code, warehouse,
		# 	(qty - work_order_qty) * conversion_factor as pending_qty, name
		# 	from `tabSales Order Item` so_item
		# 	where parent in (%s) and docstatus = 1 and qty > work_order_qty
		# 	and exists (select name from `tabBOM` bom where bom.item=so_item.item_code
		# 			and bom.is_active = 1) %s""" % \
		# 	(", ".join(["%s"] * len(so_list)), item_condition), tuple(so_list), as_dict=1)

		if self.item_code:
			item_condition = ' and so_item.item_code = "{0}"'.format(frappe.db.escape(self.item_code))

		packed_items = frappe.db.sql("""select distinct pi.parent, pi.item_code, pi.warehouse as warehouse,
			(((so_item.qty - so_item.work_order_qty) * pi.qty) / so_item.qty)
				as pending_qty, pi.parent_item, so_item.name
			from `tabSales Order Item` so_item, `tabPacked Item` pi
			where so_item.parent = pi.parent and so_item.docstatus = 1
			and pi.parent_item = so_item.item_code
			and so_item.parent in (%s) and so_item.qty > so_item.work_order_qty
			and exists (select name from `tabBOM` bom where bom.item=pi.item_code
					and bom.is_active = 1) %s""" % \
			(", ".join(["%s"] * len(so_list)), item_condition), tuple(so_list), as_dict=1)

		add_items(self,items + packed_items)
		calculate_total_planned_qty(self)

def add_items(self, items):
	# frappe.msgprint("call add")
	self.set('po_items', [])
	for data in items:
		item_details = get_item_details(data.item_code)
		pi = self.append('po_items', {
			'include_exploded_items': 1,
			'warehouse': data.warehouse,
			'item_code': data.item_code,
			'description': item_details and item_details.description or '',
			'stock_uom': item_details and item_details.stock_uom or '',
			'bom_no': item_details and item_details.bom_no or '',
			# 'planned_qty': data.pending_qty, 
			'concentration': data.concentration,
			'planned_qty':data.planned_qty,
			'pending_qty': data.pending_qty,
			'planned_start_date': now_datetime(),
			'product_bundle_item': data.parent_item
		})

		if self.get_items_from == "Sales Order":
			pi.sales_order = data.parent
			pi.sales_order_item = data.name

		elif self.get_items_from == "Material Request":
			pi.material_request = data.parent
			pi.material_request_item = data.name

def calculate_total_planned_qty(self):
		self.total_planned_qty = 0
		for d in self.po_items:
			self.total_planned_qty += flt(d.planned_qty)

