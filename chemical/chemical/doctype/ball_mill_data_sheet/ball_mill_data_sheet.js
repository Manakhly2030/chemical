// Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

cur_frm.fields_dict.product_name.get_query = function(doc) {
	return {
		filters: {
			"item_group": 'Finished Products'
		}
	}
};
cur_frm.fields_dict.sample_no.get_query = function(doc) {
	return {
		filters: {
			"product_name": doc.product_name,
			"party": doc.customer_name 
		}
	}
};
this.frm.cscript.onload = function(frm) {
	this.frm.set_query("batch_no", "items", function(doc, cdt, cdn) {
		let d = locals[cdt][cdn];
		if(!d.item_name){
			frappe.msgprint(__("Please select Item"));
		}
		else if(!d.source_warehouse){
			frappe.msgprint(__("Please select source warehouse"));
		}
		else{
			return {
				query: "chemical.batch_valuation.get_batch",
				filters: {
					'item_code': d.item_name,
					'warehouse': d.source_warehouse
				}
			}
		}
	});
}

frappe.ui.form.on('Ball Mill Data Sheet', {
	refresh: function(frm){
		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__("Outward Sample"), function() {
				frappe.model.open_mapped_doc({
					method : "chemical.chemical.doctype.ball_mill_data_sheet.ball_mill_data_sheet.make_outward_sample",
					frm : cur_frm
				})
			}, __("Make"));
		}
	}
	
});
