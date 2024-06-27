import frappe
from frappe import _
from pypika import functions as fn
from frappe.utils import flt

from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder as _WorkOrder, OverProductionError

class WorkOrder(_WorkOrder):
	def get_status(self, status=None):
		"""Return the status based on stock entries against this work order"""
		under_production = flt(frappe.db.get_single_value("Manufacturing Settings", "under_production_allowance_percentage"))

		if not status:
			status = self.status

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if status != "Stopped":
				status = "Not Started"
				if flt(self.material_transferred_for_manufacturing) > 0:
					status = "In Process"

				total_qty = flt(self.produced_qty) + flt(self.process_loss_qty)
				allowed_qty = flt(self.qty) * (100 - under_production) / 100.0 # Finbyz Changes to allow under production
				
				if flt(total_qty) >= allowed_qty:
					status = "Completed"
		else:
			status = "Cancelled"

		if (
			self.skip_transfer
			and self.produced_qty
			and self.qty > (flt(self.produced_qty) + flt(self.process_loss_qty))
		):
			status = "In Process"

		return status

@frappe.whitelist()
def make_stock_entry(work_order_id, purpose, qty=None):
	work_order = frappe.get_doc("Work Order", work_order_id)
	if not frappe.db.get_value("Warehouse", work_order.wip_warehouse, "is_group"):
		wip_warehouse = work_order.wip_warehouse
	else:
		wip_warehouse = None

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.work_order = work_order_id
	stock_entry.company = work_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = work_order.bom_no
	stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
	# accept 0 qty as well
	stock_entry.fg_completed_qty = (
		qty if qty is not None else (flt(work_order.qty) - flt(work_order.produced_qty))
	)

	if work_order.bom_no:
		stock_entry.inspection_required = frappe.db.get_value("BOM", work_order.bom_no, "inspection_required")

	if purpose == "Material Transfer for Manufacture":
		stock_entry.to_warehouse = wip_warehouse
		stock_entry.project = work_order.project
	else:
		stock_entry.from_warehouse = wip_warehouse
		stock_entry.to_warehouse = work_order.fg_warehouse
		stock_entry.project = work_order.project

	stock_entry.set_stock_entry_type()
	stock_entry.get_items()
	stock_entry.set_serial_no_batch_for_finished_good()

	if purpose=='Manufacture':
		if work_order.is_multiple_item and work_order.bom_no:
			remove_items = []
			for item in stock_entry.items:
				if item.is_finished_item:
					remove_items.append(item)
			for rm in remove_items:
				stock_entry.items.remove(rm)
			bom_multi_doc = frappe.get_doc("BOM",work_order.bom_no)
			for finish_items in bom_multi_doc.multiple_finish_item:
				# if stock_entry.items[-2].item_code == finish_items.item_code:
				# 	if stock_entry.items[-2].transfer_qty == work_order.qty:
				# 		stock_entry.items.remove(stock_entry.items[-2])
				bom = frappe.db.sql(''' select name from tabBOM where item = %s and docstatus=1''',finish_items.item_code)
				if bom:
					bom = bom[0][0]
				else:
					bom = None
				stock_entry.append("items",{
					'item_code': finish_items.item_code,
					't_warehouse': work_order.fg_warehouse,
					'qty': work_order.qty * finish_items.qty_ratio / 100,
					'uom': frappe.db.get_value('Item',finish_items.item_code,'stock_uom'),
					'stock_uom': frappe.db.get_value('Item',finish_items.item_code,'stock_uom'),
					'conversion_factor': 1 ,
					'is_finished_item': 1,
					'batch_yield':finish_items.batch_yield,
					'bom_no':bom,
					'concentration':100
				})

	return stock_entry.as_dict()
