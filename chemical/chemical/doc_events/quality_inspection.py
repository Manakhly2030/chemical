import frappe

def validate(self, method):
	update_qc(self, method)

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
		doc.db_set("quality_inspection", self.name)

		batch = frappe.get_doc("Batch", self.batch_no)
		batch.db_set("quality_inspection", self.name)

	elif self._action == "cancel":
		doc = frappe.get_doc(self.reference_type, self.reference_name)
		doc.db_set("quality_inspection", "")

		batch = frappe.get_doc("Batch", self.batch_no)
		batch.db_set("quality_inspection", "")
	

	
