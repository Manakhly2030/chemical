import datetime as dt
import json

import frappe
from frappe import _
from frappe.utils import cint, flt, cstr
from erpnext.stock.stock_ledger import get_valuation_rate
import erpnext


def batch_wise_cost():
    return cint(
        frappe.db.get_single_value(
            "Stock Settings", "exact_cost_valuation_for_batch_wise_items"
        )
    )


def validate_concentration(self, warehouse_field):
    for row in self.items:
        if not row.get(warehouse_field):
            continue

        has_batch_no = frappe.db.get_value("Item", row.item_code, "has_batch_no")
        if has_batch_no and not flt(row.concentration):
            frappe.throw(
                _(
                    "Row #{idx}. Concentration cannot be 0 for batch wise item - {item_code}.".format(
                        idx=row.idx, item_code=frappe.bold(row.item_code)
                    )
                )
            )


def make_batches(self, warehouse_field):
    # import datetime
    if self._action == "submit":
        validate_concentration(self, warehouse_field)

        for row in self.items:
            if self.doctype == "Stock Entry" and self.purpose in [
                "Material Transfer",
                "Material Transfer for Manufacture",
            ]:
                continue
            if not row.get(warehouse_field):
                continue

            has_batch_no, create_new_batch = frappe.db.get_value(
                "Item", row.item_code, ["has_batch_no", "create_new_batch"]
            )

            has_batch_no = frappe.db.get_value("Item", row.item_code, "has_batch_no")
            if has_batch_no and create_new_batch and not row.batch_no:
                if row.batch_no and flt(row.valuation_rate, 4) == flt(
                    frappe.db.get_value(
                        "Stock Ledger Entry",
                        {
                            "is_cancelled": 0,
                            "company": self.company,
                            "warehouse": row.get(warehouse_field),
                            "batch_no": row.batch_no,
                            "incoming_rate": ("!=", 0),
                        },
                        "incoming_rate",
                    ),
                    4,
                ):
                    continue

                if row.batch_no and self.doctype == "Stock Entry":
                    row.db_set("old_batch_no", row.batch_no)

                batch = frappe.new_doc("Batch")
                batch.item = row.item_code
                batch.supplier = getattr(self, "supplier", None)
                batch.lot_no = cstr(row.lot_no)
                batch.packaging_material = cstr(row.packaging_material)
                batch.packing_size = cstr(row.packing_size)
                batch.batch_yield = flt(row.batch_yield, 3)
                batch.concentration = flt(row.concentration, 3)
                batch.valuation_rate = flt(row.valuation_rate, 4)

                if self.doctype == "Stock Entry":
                    if (
                        self.stock_entry_type == "Manufacture"
                        or self.stock_entry_type == "Material Receipt"
                    ):
                        batch.manufacturing_date = self.posting_date
                try:
                    batch.posting_date = dt.datetime.strptime(
                        self.posting_date, "%Y-%m-%d"
                    ).strftime("%y%m%d")
                except:
                    batch.posting_date = self.posting_date.strftime("%y%m%d")

                batch.actual_quantity = flt(row.qty * row.conversion_factor)
                batch.reference_doctype = self.doctype
                batch.reference_name = self.name
                batch.insert()
                row.batch_no = batch.name


def validate_additional_cost(self):
    if self.purpose in ["Repack", "Manufacture"] and self._action == "submit":
        diff = abs(
            round(flt(self.value_difference, 1))
            - (round(flt(self.total_additional_costs, 1)))
        )
        if diff > 5:
            frappe.throw(
                f"ValuationError: Value difference {diff} between incoming and outgoing amount is higher than additional cost"
            )


def stock_entry_validate(self):
    if batch_wise_cost():
        if self.purpose not in [
            "Material Transfer",
            "Material Transfer for Manufacture",
        ]:
            make_batches(self, "t_warehouse")
    if self.purpose in ["Repack", "Manufacture", "Material Issue"]:
        self.get_stock_and_rate()
    if self._action == "submit":
        validate_additional_cost(self)


def set_incoming_rate(self):
    precision = cint(frappe.db.get_default("float_precision"))
    for d in self.items:
        if d.s_warehouse:
            args = self.get_args_for_incoming_rate(d)
            d.basic_rate = flt(get_incoming_rate(args), precision)
        elif not d.s_warehouse:
            d.basic_rate = 0.0
        elif self.warehouse and not d.basic_rate:
            d.basic_rate = flt(
                get_valuation_rate(
                    d.item_code,
                    self.warehouse,
                    self.doctype,
                    d.name,
                    1,
                    currency=erpnext.get_company_currency(self.company),
                ),
                precision,
            )
        d.basic_amount = d.basic_rate * d.qty


def get_incoming_rate(args, raise_error_if_no_rate=True):
    """Get Incoming Rate based on valuation method"""
    from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate

    if isinstance(args, str):
        args = json.loads(args)

    in_rate = 0
    # finbyz changes
    batch_wise_cost = cint(
        frappe.db.get_single_value(
            "Stock Settings", "exact_cost_valuation_for_batch_wise_items"
        )
    )

    # finbyz changes
    if args.get("batch_no"):
        in_rate = get_batch_rate(args.get("batch_no"))
    return in_rate


def get_batch_rate(batch_no):
    """Get Batch Valuation Rate of Batch No"""

    return flt(
        frappe.db.sql(
            """SELECT valuation_rate FROM `tabBatch` WHERE name = %s """, batch_no
        )[0][0]
    )


def stock_entry_on_cancel(self, method):
	if self.purpose in ['Material Transfer', 'Material Transfer for Manufacture']:
		delete_transfer_batches(self)
	else:
		delete_batches(self, 't_warehouse')


def delete_transfer_batches(self):
	from frappe.model.delete_doc import check_if_doc_is_linked
	
	for row in self.items:
		if row.batch_no and row.get('t_warehouse'):
			batch_no = frappe.get_doc("Batch", row.batch_no)
			if batch_no.valuation_rate == row.valuation_rate and not row.get('old_batch_no'):
				continue

			row.batch_no = row.old_batch_no
			if batch_no.reference_name == self.name:
				frappe.db.set_value("Batch",batch_no.name,'reference_name',' ')
			row.db_set('batch_no', row.old_batch_no)
			row.db_set('old_batch_no', '')

def delete_batches(self, warehouse):
	from frappe.model.delete_doc import check_if_doc_is_linked
	
	for row in self.items:
		if row.batch_no and row.get(warehouse):
			batch_no = frappe.get_doc("Batch", row.batch_no)

			if self.get('work_order') and frappe.db.get_value("Work Order", self.work_order, 'batch'):
				frappe.db.set_value("Work Order", self.work_order, 'batch', '')

			frappe.db.set_value('Batch',row.batch_no,'reference_name',None)
			row.db_set('batch_no', "")
			row.db_set('batch_no', None)
			frappe.db.set_value('Batch',row.batch_no,'disabled',1)