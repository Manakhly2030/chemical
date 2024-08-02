import frappe
from frappe import _
from frappe.utils import cint, flt

from erpnext.stock.utils import get_latest_stock_qty


def before_validate(self, method):
	calculate_qty(self)
	self.validate_fg_completed_qty()


def validate(self, method):
	set_concentration_to_100_for_non_batch_item(self)
	check_based_on_item(self)
	calculate_additional_cost(self)
	# calculate_rate_and_amount(self) #TODO
	get_based_on(self)
	calculate_target_yield(self)


def before_save(self, method):
	get_stock_rate_for_repack_and_not_from_ball_mill(self)


def before_submit(self, method):
	validate_concentration(self)
	validate_quality_inspection(self)


def on_submit(self, method):
	add_extra_items_to_work_order_items(self)
	add_items_to_work_order_finish_items(self)
	set_work_order_details(self)
	set_batch_no_in_quality_inspection(self)


def on_cancel(self, method):
	remove_items_from_work_order_finish_items(self)
	set_work_order_details(self)
	set_batch_no_in_quality_inspection(self)


def calculate_qty(self):
	for row in self.items:
		if row.get("packing_size") and row.get("no_of_packages"):
			row.qty = cint(row.packing_size) * cint(row.no_of_packages)


def set_concentration_to_100_for_non_batch_item(self):
	for row in self.items:
		if row.item_code and not row.batch_no:
			row.concentration = 100


def check_based_on_item(self):
	if (
		self.purpose == "Manufacture"
		and frappe.db.get_value("BOM", self.bom_no, "based_on")
		and self.based_on not in [item.item_code for item in self.items]
	):
		frappe.throw(
			f"Based on Item {frappe.bold(self.based_on)} Required in Raw Materials"
		)


def calculate_additional_cost(self):
	for row in self.additional_costs or []:
		if row.uom == "FG QTY":
			row.qty = self.fg_completed_qty

		if row.qty and row.rate:
			row.amount = flt(row.qty) * flt(row.rate)
			row.base_amount = flt(row.qty) * flt(row.rate)


def get_based_on(self):
	if self.work_order:
		self.based_on = frappe.db.get_value("Work Order", self.work_order, "based_on")


def calculate_target_yield(self):
	cal_yield = 0
	item_arr = []
	item_map = {}
	flag = 0

	if self.purpose == "Manufacture" and self.based_on:
		for row in self.items:
			if row.t_warehouse:
				flag += 1

			if row.item_code not in item_arr:
				item_map.setdefault(row.item_code, {"qty": 0, "yield_weights": 0})

			# item_map[row.item_code]['quantity'] += flt(row.quantity)
			item_map[row.item_code]["qty"] += flt(row.qty)
			item_map[row.item_code]["yield_weights"] += flt(row.batch_yield) * flt(row.qty)

		if flag == 1:
			# Last row object
			last_row = self.items[-1]

			# Check if items list has frm.doc.based_on value
			if self.based_on in [row.item_code for row in self.items]:
				cal_yield = flt(last_row.qty / item_map[self.based_on]["qty"])

			last_row.batch_yield = flt(cal_yield)


def get_stock_rate_for_repack_and_not_from_ball_mill(self):
	if self.purpose == "Repack" and not self.from_ball_mill:
		self.get_stock_and_rate()


def validate_concentration(self):
	if self.work_order and self.purpose == "Manufacture":
		production_item = frappe.db.get_value(
			"Work Order", self.work_order, "production_item"
		)
		for row in self.items:
			if (
				row.t_warehouse
				and row.item_code == production_item
				and not row.concentration
			):
				frappe.throw(
					_(f"Add concentration in row {row.idx} for item {row.item_code}")
				)


def validate_quality_inspection(self):
	if (
		self.purpose == "Manufacture"
		and self.bom_no
		and frappe.db.get_value("BOM", self.bom_no, "inspection_required")
	):
		for row in self.items:
			if row.t_warehouse and not row.quality_inspection:
				frappe.throw(
					_(
						f"Quality Inspection is mandatory in row {row.idx} for item {row.item_code}."
					)
				)


def add_extra_items_to_work_order_items(self):
	if self.purpose == "Manufacture" and self.work_order:
		work_order = frappe.get_doc("Work Order", self.work_order)
		for row in self.items:
			if (
				row.s_warehouse
				and not row.t_warehouse
				and row.item_code
				not in [d.item_code for d in work_order.required_items]
			):
				work_order.append(
					"required_items",
					{
						"item_code": row.item_code,
						"item_name": row.item_name,
						"description": row.description,
						"source_warehouse": row.s_warehouse,
						"required_qty": row.qty,
						"transferred_qty": row.qty,
						"valuation_rate": row.valuation_rate,
						"available_qty_at_source_warehouse": get_latest_stock_qty(
							row.item_code, row.s_warehouse
						),
					},
				)

		for row in work_order.required_items:
			work_order.db_update()


def add_items_to_work_order_finish_items(self):
	if self.purpose == "Manufacture" and self.work_order:
		work_order = frappe.get_doc("Work Order", self.work_order)
		bom = frappe.get_doc("BOM", work_order.bom_no)
		if bom.multiple_finish_item:
			items = {
				row.item_code: (row.cost_ratio, row.qty_ratio, row.batch_yield)
				for row in bom.multiple_finish_item
			}
		else:
			items = {work_order.production_item: (100, 100, bom.batch_yield)}

		for row in self.items:
			if row.t_warehouse and row.item_code in items:
				data = items[row.item_code]
				work_order.append(
					"finish_item",
					{
						"item_code": row.item_code,
						"actual_qty": row.qty,
						"actual_valuation": row.valuation_rate,
						"lot_no": row.lot_no,
						"purity": row.concentration,
						"packing_size": row.packing_size,
						"no_of_packages": row.no_of_packages,
						"batch_yield": row.batch_yield,
						"batch_no": row.batch_no,
						"bom_cost_ratio": data[0],
						"bom_qty_ratio": data[1],
						"bom_qty": work_order.qty * data[1] / 100,
						"bom_yield": data[2],
						"stock_entry": self.name,
						"se_detail": row.name,
					},
				)
		work_order.flags.ignore_permissions = True
		work_order.flags.ignore_validate_update_after_submit = True
		work_order.save()


def set_batch_no_in_quality_inspection(self):
	for row in self.items:
		if row.quality_inspection:
			qi_doc = frappe.get_doc("Quality Inspection", row.quality_inspection)
			qi_doc.db_set("batch_no", row.batch_no, update_modified=False)


def remove_items_from_work_order_finish_items(self):
	if self.purpose == "Manufacture" and self.work_order:
		work_order = frappe.get_doc("Work Order", self.work_order)

		data = []

		for row in work_order.finish_item:
			if row.stock_entry != self.name:
				data.append(
					{
						"item_code": row.item_code,
						"actual_qty": row.actual_qty,
						"actual_valuation": row.actual_valuation,
						"lot_no": row.lot_no,
						"purity": row.purity,
						"packing_size": row.packing_size,
						"no_of_packages": row.no_of_packages,
						"batch_yield": row.batch_yield,
						"batch_no": row.batch_no,
						"bom_cost_ratio": row.bom_cost_ratio,
						"bom_qty_ratio": row.bom_qty_ratio,
						"bom_qty": row.bom_qty,
						"bom_yield": row.bom_yield,
						"stock_entry": row.stock_entry,
						"se_detail": row.se_detail,
					}
				)

		work_order.finish_item = []
		for row in data:
			work_order.append("finish_item", row)

		work_order.flags.ignore_permissions = True
		work_order.flags.ignore_validate_update_after_submit = True
		work_order.save()


def set_work_order_details(self):
	if self.purpose == "Manufacture" and self.work_order:
		work_order = frappe.get_doc("Work Order", self.work_order)

		count = len(work_order.finish_item)
		batch_yield = 0
		concentration = 0
		lot_nos = []

		for row in work_order.finish_item:
			batch_yield += flt(row.batch_yield)
			concentration += flt(row.purity)
			if row.lot_no:
				lot_nos.append(row.lot_no)

		work_order.db_set("batch_yield", flt(batch_yield / (count or 1)))
		work_order.db_set("concentration", flt(concentration / (count or 1)))
		work_order.db_set("lot_no", ", ".join(lot_nos))
