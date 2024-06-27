import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as _StockEntry


# TODO: need to check with default function
def add_additional_cost(doc, self, qty=None):
	maintain_as_is_new = frappe.db.get_value("Company",self.company,'maintain_as_is_new')
	qty = flt(qty)
	abbr = frappe.db.get_value("Company",self.company,'abbr')
	bom = frappe.get_doc("BOM",self.bom_no)

	for additional_cost in bom.additional_cost:
		additional_cost_dict = {}
		if additional_cost.uom == "FG QTY":
			qty = flt(doc.fg_completed_qty if maintain_as_is_new else doc.fg_completed_quantity)
			additional_cost_dict['uom'] = "FG QTY"
		else:
			qty = (qty *flt(additional_cost.qty)) / flt(bom.qty) if maintain_as_is_new else (qty *flt(additional_cost.qty)) / flt(bom.quantity)
		
		additional_cost_dict["expense_account"] = 'Expenses Included In Valuation - {}'.format(abbr)
		additional_cost_dict["description"] = additional_cost.description
		additional_cost_dict["qty"] = qty
		additional_cost_dict["rate"] = additional_cost.rate
		additional_cost_dict["amount"] = qty * flt(additional_cost.rate)
		additional_cost_dict["base_amount"] = qty * flt(additional_cost.rate)
		
		doc.append("additional_costs", additional_cost_dict)

class StockEntry(_StockEntry):
	@frappe.whitelist()
	def get_items(self):
		self.set("items", [])
		self.validate_work_order()

		if not self.posting_date or not self.posting_time:
			frappe.throw(_("Posting date and posting time is mandatory"))

		self.set_work_order_details()
		self.flags.backflush_based_on = frappe.db.get_single_value(
			"Manufacturing Settings", "backflush_raw_materials_based_on"
		)

		if self.bom_no:
			backflush_based_on = frappe.db.get_single_value(
				"Manufacturing Settings", "backflush_raw_materials_based_on"
			)

			if self.purpose in [
				"Material Issue",
				"Material Transfer",
				"Manufacture",
				"Repack",
				"Send to Subcontractor",
				"Material Transfer for Manufacture",
				"Material Consumption for Manufacture",
			]:
				if self.work_order and self.purpose == "Material Transfer for Manufacture":
					item_dict = self.get_pending_raw_materials(backflush_based_on)
					if self.to_warehouse and self.pro_doc:
						for item in item_dict.values():
							item["to_warehouse"] = self.pro_doc.wip_warehouse
					self.add_to_stock_entry_detail(item_dict)

				elif (
					self.work_order
					and (
						self.purpose == "Manufacture"
						or self.purpose == "Material Consumption for Manufacture"
					)
					and not self.pro_doc.skip_transfer
					and self.flags.backflush_based_on == "Material Transferred for Manufacture"
				):
					self.add_transfered_raw_materials_in_items()

				elif (
					self.work_order
					and (
						self.purpose == "Manufacture"
						or self.purpose == "Material Consumption for Manufacture"
					)
					and self.flags.backflush_based_on == "BOM"
					and frappe.db.get_single_value("Manufacturing Settings", "material_consumption") == 1
				):
					self.get_unconsumed_raw_materials()

				else:
					if not self.fg_completed_qty:
						frappe.throw(_("Manufacturing Quantity is mandatory"))

					item_dict = self.get_bom_raw_materials(self.fg_completed_qty)

					# Get Subcontract Order Supplied Items Details
					if (
						self.get(self.subcontract_data.order_field)
						and self.purpose == "Send to Subcontractor"
					):
						# Get Subcontract Order Supplied Items Details
						parent = frappe.qb.DocType(self.subcontract_data.order_doctype)
						child = frappe.qb.DocType(self.subcontract_data.order_supplied_items_field)

						item_wh = (
							frappe.qb.from_(parent)
							.inner_join(child)
							.on(parent.name == child.parent)
							.select(child.rm_item_code, child.reserve_warehouse)
							.where(parent.name == self.get(self.subcontract_data.order_field))
						).run(as_list=True)

						item_wh = frappe._dict(item_wh)

					for item in item_dict.values():
						if self.pro_doc and cint(self.pro_doc.from_wip_warehouse):
							item["from_warehouse"] = self.pro_doc.wip_warehouse
						# Get Reserve Warehouse from Subcontract Order
						if (
							self.get(self.subcontract_data.order_field)
							and self.purpose == "Send to Subcontractor"
						):
							item["from_warehouse"] = item_wh.get(item.item_code)
						item["to_warehouse"] = (
							self.to_warehouse if self.purpose == "Send to Subcontractor" else ""
						)

					self.add_to_stock_entry_detail(item_dict)

			# fetch the serial_no of the first stock entry for the second stock entry
			if self.work_order and self.purpose == "Manufacture":
				work_order = frappe.get_doc("Work Order", self.work_order)
				add_additional_cost(self, work_order)

			# add finished goods item
			if self.purpose in ("Manufacture", "Repack"):
				self.set_process_loss_qty()
				self.load_items_from_bom()

		self.set_scrap_items()
		self.set_actual_qty()
		self.validate_customer_provided_item()
		self.calculate_rate_and_amount(raise_error_if_no_rate=False)
