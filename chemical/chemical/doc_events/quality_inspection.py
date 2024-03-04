import frappe

def validate(self, method):
	update_qc(self, method)

def validate_qc(self, method):
	set_details_in_qc(self, method)

def on_cancel(self, method):
	update_qc(self, method)

def update_qc_reference(self):
	quality_inspection = self.name if self.docstatus == 1 else ""
	doctype = self.reference_type + ' Item'
	if self.reference_type == 'Stock Entry':
		doctype = 'Stock Entry Detail'
	
	if self.reference_type == "Outward Sample":
		doctype = 'Outward Sample Details'

	if self.reference_type == "Outward Sample":
		doctype = 'Inward Sample Details'


	if self.reference_type not in ["Outward Sample","Inward Sample"]:
		if self.reference_type and self.reference_name:
			conditions = ""
			if self.batch_no and self.docstatus == 1:
				conditions += " and t1.batch_no = '%s'"%(self.batch_no)

			# if self.lot_no and self.docstatus == 1:
			# 	conditions += " and t1.lot_no = '%s'"%(self.lot_no)

			if self.docstatus == 2: # if cancel, then remove qi link wherever same name
				conditions += " and t1.quality_inspection = '%s'"%(self.name)

			frappe.db.sql("""
				UPDATE
					`tab{child_doc}` t1, `tab{parent_doc}` t2
				SET
					t1.quality_inspection = %s, t2.modified = %s
				WHERE
					t1.parent = %s
					and t1.item_code = %s
					and t1.parent = t2.name
					{conditions}
			""".format(parent_doc=self.reference_type, child_doc=doctype, conditions=conditions),
				(quality_inspection, self.modified, self.reference_name, self.item_code))
			

def update_qc(self, method):
	if self._action == "submit":
		doc = frappe.get_doc(self.reference_type, self.reference_name)
		meta = frappe.get_meta(self.reference_type)
		if meta.has_field('quality_inspection'):
			doc.db_set("quality_inspection", self.name)

		if self.batch_no:
			meta_batch = frappe.get_meta("Batch")
			batch = frappe.get_doc("Batch", self.batch_no)
			if meta_batch.has_field('quality_inspection'):
				batch.db_set("quality_inspection", self.name)

	elif self._action == "cancel":
		doc = frappe.get_doc(self.reference_type, self.reference_name)
		meta = frappe.get_meta(self.reference_type)
		if meta.has_field('quality_inspection'):
			doc.db_set("quality_inspection", self.name)
		# doc.db_set("quality_inspection", "")
				
		if self.batch_no:
			meta_batch = frappe.get_meta("Batch")
			batch = frappe.get_doc("Batch", self.batch_no)
			if meta_batch.has_field('quality_inspection'):
				batch.db_set("quality_inspection", "")
	
def set_details_in_qc(self, method):
	if self.reference_type == "Purchase Receipt":
		doc = frappe.get_doc("Purchase Receipt", self.reference_name)
		for row in doc.items:
			if row.item_code == self.item_code:
				self.lot_no = row.lot_no
				self.packaging_material = row.packaging_material
				self.concentration = row.concentration
				self.packing_size = row.packing_size
				self.no_of_packages = row.no_of_packages
				self.qty = row.qty
	
	if self.reference_type == "Delivery Note":
		doc = frappe.get_doc("Delivery Note", self.reference_name)
		for row in doc.items:
			if row.item_code == self.item_code:
				self.lot_no = row.lot_no
				self.packaging_material = row.packaging_material
				self.concentration = row.concentration
				self.packing_size = row.packing_size
				self.no_of_packages = row.no_of_packages
				self.qty = row.qty
	
	if self.reference_type == "Stock Entry":
		doc = frappe.get_doc("Stock Entry", self.reference_name)
		for row in doc.items:
			if row.item_code == self.item_code:
				self.lot_no = row.lot_no
				self.packaging_material = row.packaging_material
				self.concentration = row.concentration
				self.packing_size = row.packing_size
				self.no_of_packages = row.no_of_packages
				self.qty = row.qty