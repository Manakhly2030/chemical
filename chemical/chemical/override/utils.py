import frappe
from frappe.utils import flt, cint
import datetime


def make_batches(self, warehouse_field):
    for d in self.items:
        if self.doctype == "Stock Entry" and self.purpose in [
            "Material Transfer",
            "Material Transfer for Manufacture",
        ]:
            continue
        # TODO: Check if this is needed (commented all code below)
        # if d.batch_no and flt(d.valuation_rate, 4) == flt(
        #     frappe.db.get_value(
        #         "Stock Ledger Entry",
        #         {
        #             "is_cancelled": 0,
        #             "company": self.company,
        #             "warehouse": d.get(warehouse_field),
        #             "batch_no": d.batch_no,
        #             "incoming_rate": ("!=", 0),
        #         },
        #         "incoming_rate",
        #     ),
        #     4,
        # ):
        #     continue
        # TODO: Check if this is needed (commented all code below)
        if d.batch_no and self.doctype == "Stock Entry":
            d.db_set("old_batch_no", d.batch_no)
        if d.get(warehouse_field):
            has_batch_no, create_new_batch = frappe.db.get_value(
                "Item", d.item_code, ["has_batch_no", "create_new_batch"]
            )
            if has_batch_no and create_new_batch and d.batch_no:
                batch = frappe.get_doc("Batch", d.batch_no)
                batch.db_set("concentration", d.get("concentration"))
                batch.db_set("lot_no", d.get("lot_no"))
                batch.db_set("valuation_rate", d.get("valuation_rate"))
                batch.db_set("packaging_material", d.get("packaging_material"))
                batch.db_set("packing_size", d.get("packing_size"))
                batch.db_set("batch_yield", d.get("batch_yield"))

            if has_batch_no and create_new_batch and not d.batch_no:
                doc = frappe.new_doc("Batch")
                doc.item = d.item_code
                doc.supplier = getattr(self, "supplier", None)
                doc.reference_doctype = self.doctype
                doc.reference_name = self.name
                doc.concentration = d.get("concentration")
                doc.lot_no = d.get("lot_no")
                doc.valuation_rate = d.get("valuation_rate")
                doc.packaging_material = d.get("packaging_material")
                doc.packing_size = d.get("packing_size")
                doc.uv_value = d.get("uv_value")
                doc.batch_yield = d.get("batch_yield")
                doc.manufacturing_date = self.posting_date
                doc.save()

                d.batch_no = doc.name

def se_cal_rate_qty(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		doc_items = frappe.get_doc({"doctype": "Stock Entry Detail"})
		for d in self.items:
			maintain_as_is_stock = frappe.db.get_value(
				"Item", d.item_code, "maintain_as_is_stock"
			)
			if maintain_as_is_stock:
				if not d.concentration and d.t_warehouse:
					frappe.throw(
						"{} Row: {} Please add concentration".format(d.doctype, d.idx)
					)
			concentration = 100
			if d.batch_no:
				concentration = (
					frappe.db.get_value("Batch", d.batch_no, "concentration") or 100
				)
			else:
				concentration = d.concentration or 100
			if d.get("packing_size") and d.get("no_of_packages"):
				d.qty = d.packing_size * d.no_of_packages
				if maintain_as_is_stock:
					d.quantity = flt(d.qty) * flt(concentration) / 100
					if d.price and not d.set_basic_rate_manually:
						d.basic_rate = flt(d.quantity) * flt(d.price) / flt(d.qty)
				else:
					d.quantity = d.qty
					if d.price and not d.set_basic_rate_manually:
						d.basic_rate = d.price
			else:
				if maintain_as_is_stock:
					if d.quantity:
						d.qty = flt((d.quantity * 100.0) / concentration)

					if d.qty and not d.quantity:
						d.quantity = d.qty * concentration / 100.0

					if d.price and not d.set_basic_rate_manually:
						d.basic_rate = flt(d.quantity) * flt(d.price) / flt(d.qty)
				else:
					if d.quantity:
						d.qty = d.quantity

					if d.qty and not d.quantity:
						d.quantity = d.qty

					if d.price and not d.set_basic_rate_manually:
						d.basic_rate = d.price
	else:
		for d in self.items:
			if not d.get("ignore_calculation"):
				maintain_as_is_stock = frappe.db.get_value(
					"Item", d.item_code, "maintain_as_is_stock"
				)
				if maintain_as_is_stock:
					if d.get('packing_size') and d.get("no_of_packages") and d.get("concentration"):
						if self.get("is_return"):
							d.no_of_packages = -abs(d.no_of_packages)
						d.qty = (flt(d.packing_size) * flt(d.no_of_packages) * flt(d.concentration)) / 100.0
				else:
					if d.get("packing_size") and d.get("no_of_packages"):
						d.qty = cint(d.packing_size) * cint(d.no_of_packages)
						d.receive_qty = d.packing_size * d.no_of_packages
			else:
				if d.get("packing_size") and d.get("no_of_packages"):
					d.qty = cint(d.packing_size) * cint(d.no_of_packages)

def se_repack_cal_rate_qty(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		for d in self.items:
			doc_items = frappe.get_doc({"doctype": "Stock Entry Detail"})
			maintain_as_is_stock = frappe.db.get_value(
				"Item", d.item_code, "maintain_as_is_stock"
			)
			packing_size = 0
			if not d.s_warehouse:
				if hasattr(doc_items, "receive_qty"):
					if hasattr(doc_items, "tare_weight"):
						if hasattr(doc_items, "receive_packing_size") and hasattr(
							doc_items, "receive_no_of_packages"
						):
							packing_size = flt(d.receive_packing_size) - flt(d.tare_weight)
							d.receive_qty = flt(packing_size) * flt(
								d.receive_no_of_packages
							)
					else:
						if hasattr(doc_items, "receive_packing_size") and hasattr(
							doc_items, "receive_no_of_packages"
						):
							packing_size = flt(d.receive_packing_size)
							d.receive_qty = flt(packing_size) * flt(
								d.receive_no_of_packages
							)
				else:
					if d.packing_size and d.no_of_packages:
						d.qty = received_qty = flt(d.packing_size) * flt(d.no_of_packages)

				if hasattr(doc_items, "accepted_qty"):
					if hasattr(doc_items, "accepted_packing_size") and hasattr(
						doc_items, "accepted_no_of_packages"
					):
						d.accepted_qty = flt(d.accepted_packing_size) * flt(
							d.accepted_no_of_packages
						)

				if hasattr(doc_items, "supplier_qty"):
					if hasattr(doc_items, "supplier_packing_size") and hasattr(
						doc_items, "supplier_no_of_packages"
					):
						d.supplier_qty = flt(d.supplier_packing_size) * flt(
							d.supplier_no_of_packages
						)
					if not d.supplier_qty:
						frappe.throw(
							"{} Row: {} Please add supplier Qty".format(d.doctype, d.idx)
						)

				if hasattr(doc_items, "receive_packing_size"):
					if hasattr(doc_items, "accepted_packing_size"):
						d.packing_size = flt(d.accepted_packing_size) or flt(packing_size)
						d.no_of_packages = flt(d.accepted_no_of_packages) or flt(
							d.receive_no_of_packages
						)
					else:
						d.packing_size = flt(packing_size)
						d.no_of_packages = flt(d.receive_no_of_packages)

				if maintain_as_is_stock:
					if hasattr(doc_items, "received_concentration"):
						d.receive_quantity = (
							flt(d.receive_qty) * flt(d.received_concentration) / 100
						)
					if hasattr(doc_items, "supplier_concentration"):
						if not d.supplier_concentration:
							frappe.throw(
								"{} Row: {} Please add supplier concentration".format(
									d.doctype, d.idx
								)
							)
						d.supplier_quantity = (
							flt(d.supplier_qty) * flt(d.supplier_concentration) / 100
						)
					if hasattr(doc_items, "accepted_concentration"):
						d.accepted_quantity = (
							flt(d.accepted_qty) * flt(d.accepted_concentration) / 100
						)

					if hasattr(doc_items, "accepted_qty") and hasattr(
						doc_items, "receive_qty"
					):
						d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
					if hasattr(doc_items, "accepted_concentration") and hasattr(
						doc_items, "received_concentration"
					):
						d.concentration = flt(d.accepted_concentration) or flt(
							d.received_concentration
						)

					if not d.qty:
						if hasattr(doc_items, "receive_qty"):
							frappe.throw(
								"{} Row: {} Please add Receive Qty or Accepted Qty".format(
									d.doctype, d.idx
								)
							)
						else:
							frappe.throw(
								"{} Row: {} Please add Qty".format(d.doctype, d.idx)
							)
					if not d.concentration:
						if hasattr(doc_items, "received_concentration"):
							frappe.throw(
								"{} Row: {} Please add received or accepted concentration".format(
									d.doctype, d.idx
								)
							)
						else:
							frappe.throw(
								"{} Row: {} Please add concentration".format(
									d.doctype, d.idx
								)
							)

					if hasattr(doc_items, "accepted_quantity") and hasattr(
						doc_items, "receive_quantity"
					):
						d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)
					else:
						d.quantity = flt(d.qty) * flt(d.concentration) / 100
					if hasattr(doc_items, "supplier_quantity"):
						d.basic_rate = flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)

				else:
					if hasattr(doc_items, "received_concentration"):
						d.receive_quantity = flt(d.receive_qty)
					if hasattr(doc_items, "supplier_concentration"):
						d.supplier_quantity = flt(d.supplier_qty)
					if hasattr(doc_items, "accepted_concentration"):
						d.accepted_quantity = flt(d.accepted_qty)

					if hasattr(doc_items, "accepted_qty") and hasattr(
						doc_items, "receive_qty"
					):
						d.qty = flt(d.accepted_qty) or flt(d.receive_qty)
					if hasattr(doc_items, "accepted_concentration") and hasattr(
						doc_items, "received_concentration"
					):
						d.concentration = flt(d.accepted_concentration) or flt(
							d.received_concentration
						)

					if not d.qty:
						if hasattr(doc_items, "receive_qty"):
							frappe.throw(
								"{} Row: {} Please add Receive Qty or Accepted Qty".format(
									d.doctype, d.idx
								)
							)
						else:
							frappe.throw(
								"{} Row: {} Please add Qty".format(d.doctype, d.idx)
							)

					if hasattr(doc_items, "accepted_quantity") and hasattr(
						doc_items, "receive_quantity"
					):
						d.quantity = flt(d.accepted_quantity) or flt(d.receive_quantity)
					else:
						d.quantity = flt(d.qty)
					if d.price and not d.set_basic_rate_manually:
						d.basic_rate = flt(d.price)

				if hasattr(doc_items, "short_quantity"):
					d.short_quantity = flt(d.quantity) - flt(d.supplier_quantity)
					if d.short_quantity:
						d.rate = flt(d.supplier_quantity) * flt(d.price) / flt(d.qty)

				if hasattr(doc_items, "amount_difference"):
					d.amount_difference = flt(d.price) * flt(d.short_quantity)

			else:
				if maintain_as_is_stock:
					if not d.concentration and d.t_warehouse:
						frappe.throw(
							"{} Row: {} Please add concentration".format(d.doctype, d.idx)
						)
					concentration = 100
					if d.batch_no:
						concentration = (
							frappe.db.get_value("Batch", d.batch_no, "concentration") or 100
						)
					else:
						concentration = d.concentration or 100
				if d.get("packing_size") and d.get("no_of_packages"):
					d.qty = d.packing_size * d.no_of_packages
					if maintain_as_is_stock:
						d.quantity = d.qty * concentration / 100
						if d.price and not d.set_basic_rate_manually:
							d.basic_rate = flt(d.quantity) * flt(d.price) / flt(d.qty)
					else:
						d.quantity = d.qty
						if d.price and not d.set_basic_rate_manually:
							d.basic_rate = d.price
				else:
					if maintain_as_is_stock:
						if d.quantity:
							d.qty = flt((d.quantity * 100.0) / concentration)

						if d.qty and not d.quantity:
							d.quantity = d.qty * concentration / 100.0

						if d.price and not d.set_basic_rate_manually:
							d.basic_rate = flt(d.quantity) * flt(d.price) / flt(d.qty)
					else:
						if d.quantity:
							d.qty = d.quantity

						if d.qty and not d.quantity:
							d.quantity = d.qty

						if d.price and not d.set_basic_rate_manually:
							d.basic_rate = d.price
	else:
		for d in self.items:
			if not d.get("ignore_calculation"):
				maintain_as_is_stock = frappe.db.get_value(
					"Item", d.item_code, "maintain_as_is_stock"
				)
				if maintain_as_is_stock:
					if d.get('packing_size') and d.get("no_of_packages") and d.get("concentration"):
						if self.get("is_return"):
							d.no_of_packages = -abs(d.no_of_packages)
						d.qty = (flt(d.packing_size) * flt(d.no_of_packages) * flt(d.concentration)) / 100.0
				else:
					if d.get("packing_size") and d.get("no_of_packages"):
						d.qty = d.packing_size * d.no_of_packages
						d.receive_qty = d.packing_size * d.no_of_packages
			else:
				if d.get("packing_size") and d.get("no_of_packages"):
						d.qty = d.packing_size * d.no_of_packages

def cal_actual_valuations(self):
	for row in self.items:
		maintain_as_is_stock = frappe.db.get_value(
			"Item", row.item_code, "maintain_as_is_stock"
		)
		if maintain_as_is_stock:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt(
				(flt(row.valuation_rate) * 100) / concentration
			)
		else:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt(row.valuation_rate)
