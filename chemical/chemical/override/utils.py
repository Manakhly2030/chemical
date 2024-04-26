import frappe
from frappe.utils import flt
import datetime


def make_batches(self, warehouse_field):
    """Create batches if required. Called before submit"""
    for d in self.items:
        if self.doctype == 'Stock Entry' and self.purpose in ['Material Transfer', 'Material Transfer for Manufacture']:
            continue
        if d.batch_no and flt(d.valuation_rate,4) == flt(frappe.db.get_value("Stock Ledger Entry", {'is_cancelled':0,'company':self.company,'warehouse':d.get(warehouse_field),'batch_no':d.batch_no,'incoming_rate':('!=', 0)},'incoming_rate'),4):
            continue
        if d.batch_no and self.doctype == "Stock Entry":
            d.db_set('old_batch_no', d.batch_no)
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
