import frappe
from frappe import _
from pypika import functions as fn
from frappe.utils import flt

from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder as _WorkOrder, OverProductionError

class WorkOrder(_WorkOrder):
	def update_transferred_qty_for_required_items(self):
		maintain_as_is_new = frappe.db.get_value("Company", self.company, "maintain_as_is_new")
		ste = frappe.qb.DocType("Stock Entry")
		ste_child = frappe.qb.DocType("Stock Entry Detail")

		query = (
			frappe.qb.from_(ste)
			.inner_join(ste_child)
			.on(ste_child.parent == ste.name)
			.select(
				ste_child.item_code,
				ste_child.original_item,
				fn.Sum(ste_child.qty if maintain_as_is_new else ste_child.quantity).as_("qty"),
			)
			.where(
				(ste.docstatus == 1)
				& (ste.work_order == self.name)
				& (ste.purpose == "Material Transfer for Manufacture")
				& (ste.is_return == 0)
			)
			.groupby(ste_child.item_code)
		)

		data = query.run(as_dict=1) or []
		transferred_items = frappe._dict({d.original_item or d.item_code: d.qty for d in data})

		for row in self.required_items:
			row.db_set(
				"transferred_qty", (transferred_items.get(row.item_code) or 0.0), update_modified=False
			)
	
	def update_returned_qty(self):
		maintain_as_is_new = frappe.db.get_value("Company", self.company, "maintain_as_is_new")
		ste = frappe.qb.DocType("Stock Entry")
		ste_child = frappe.qb.DocType("Stock Entry Detail")

		query = (
			frappe.qb.from_(ste)
			.inner_join(ste_child)
			.on(ste_child.parent == ste.name)
			.select(
				ste_child.item_code,
				ste_child.original_item,
				fn.Sum(ste_child.qty).as_("qty") if maintain_as_is_new else fn.Sum(ste_child.quantity).as_("qty"),
			)
			.where(
				(ste.docstatus == 1)
				& (ste.work_order == self.name)
				& (ste.purpose == "Material Transfer for Manufacture")
				& (ste.is_return == 1)
			)
			.groupby(ste_child.item_code)
		)

		data = query.run(as_dict=1) or []
		returned_dict = frappe._dict({d.original_item or d.item_code: d.qty for d in data})

		for row in self.required_items:
			row.db_set("returned_qty", (returned_dict.get(row.item_code) or 0.0), update_modified=False)
	
	def update_consumed_qty_for_required_items(self):
		"""
		Update consumed qty from submitted stock entries
		against a work order for each stock item
		"""

		maintain_as_is_new = frappe.db.get_value("Company", self.company, "maintain_as_is_new")
		select_field = "SUM(detail.qty)" if maintain_as_is_new else "SUM(detail.quantity)"

		for item in self.required_items:
			consumed_qty = frappe.db.sql(
				f"""
				SELECT
					{select_field}
				FROM
					`tabStock Entry` entry,
					`tabStock Entry Detail` detail
				WHERE
					entry.work_order = %(name)s
						AND (entry.purpose = "Material Consumption for Manufacture"
							OR entry.purpose = "Manufacture")
						AND entry.docstatus = 1
						AND detail.parent = entry.name
						AND detail.s_warehouse IS NOT null
						AND (detail.item_code = %(item)s
							OR detail.original_item = %(item)s)
				""",
				{"name": self.name, "item": item.item_code},
			)[0][0]

			item.db_set("consumed_qty", flt(consumed_qty), update_modified=False)
	
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

	def validate_qty(self):
		if not self.qty > 0:
			frappe.throw(_("Quantity to Manufacture must be greater than 0."))

		if self.production_plan and self.production_plan_item and not self.production_plan_sub_assembly_item:
			qty_dict = frappe.db.get_value(
				"Production Plan Item", self.production_plan_item, ["planned_qty", "ordered_qty"], as_dict=1
			)

			if not qty_dict:
				return

			allowance_qty = (
				flt(
					frappe.db.get_single_value(
						"Manufacturing Settings", "overproduction_percentage_for_work_order"
					)
				)
				/ 100
				* qty_dict.get("planned_qty", 0)
			)

			max_qty = qty_dict.get("planned_qty", 0) + allowance_qty - qty_dict.get("ordered_qty", 0)

			# Finbyz Changes Removed Over Production Error
			# TODO: Check if required
			# if not max_qty > 0:
			# 	frappe.throw(
			# 		_("Cannot produce more item for {0}").format(self.production_item), OverProductionError
			# 	)
			# elif self.qty > max_qty:
			# 	frappe.throw(
			# 		_("Cannot produce more than {0} items for {1}").format(max_qty, self.production_item),
			# 		OverProductionError,
			# 	)