import frappe
from frappe.utils import cint, flt
from frappe import _

from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry as _StockEntry
# from erpnext.manufacturing.doctype.bom.bom import add_additional_cost # TODO: Check This
from chemical.chemical.override.utils import make_batches


def add_additional_cost(stock_entry,self,qty=None):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		abbr = frappe.db.get_value("Company",self.company,'abbr')
		bom = frappe.get_doc("BOM",self.bom_no)
		for additional_cost in bom.additional_cost:
			if additional_cost.uom == "FG QTY":
				stock_entry.append("additional_costs",{
					'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
					'description': additional_cost.description,
					'qty': stock_entry.fg_completed_quantity,
					'rate': additional_cost.rate,
					'amount': flt(additional_cost.rate) * flt(stock_entry.fg_completed_quantity),
					'base_amount':flt(additional_cost.rate) * flt(stock_entry.fg_completed_quantity),
					'uom':"FG QTY"
				})
			else:
				stock_entry.append("additional_costs",{
					'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
					'description': additional_cost.description,
					'qty': (flt((flt(qty)*flt(additional_cost.qty))/flt(bom.quantity))),
					'rate': additional_cost.rate,
					'amount': (flt((flt(qty)*flt(additional_cost.qty))/flt(bom.quantity)))*flt(additional_cost.rate),
					'base_amount':(flt((flt(qty)*flt(additional_cost.qty))/flt(bom.quantity)))*flt(additional_cost.rate)
				})
	else:
		abbr = frappe.db.get_value("Company",self.company,'abbr')
		bom = frappe.get_doc("BOM",self.bom_no)
		for additional_cost in bom.additional_cost:
			if additional_cost.uom == "FG QTY":
				stock_entry.append("additional_costs",{
					'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
					'description': additional_cost.description,
					'qty': stock_entry.fg_completed_qty,
					'rate': additional_cost.rate,
					'amount': flt(additional_cost.rate) * flt(stock_entry.fg_completed_qty),
					'base_amount':flt(additional_cost.rate) * flt(stock_entry.fg_completed_qty),
					'uom':"FG QTY"
				})
			else:
				stock_entry.append("additional_costs",{
					'expense_account': 'Expenses Included In Valuation - {}'.format(abbr),
					'description': additional_cost.description,
					'qty': (flt((flt(qty)*flt(additional_cost.qty))/flt(bom.qty))),
					'rate': additional_cost.rate,
					'amount': (flt((flt(qty)*flt(additional_cost.qty))/flt(bom.qty)))*flt(additional_cost.rate),
					'base_amount':(flt((flt(qty)*flt(additional_cost.qty))/flt(bom.qty)))*flt(additional_cost.rate)
				})


class StockEntry(_StockEntry):
	def make_batches(self, warehouse_field):
		return make_batches(self, warehouse_field)
	
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
				add_additional_cost(self, work_order, self.fg_completed_qty) # Finbyz Changes

			# add finished goods item
			if self.purpose in ("Manufacture", "Repack"):
				self.set_process_loss_qty()
				self.load_items_from_bom()

		self.set_scrap_items()
		self.set_actual_qty()
		self.validate_customer_provided_item()
		self.calculate_rate_and_amount(raise_error_if_no_rate=False)