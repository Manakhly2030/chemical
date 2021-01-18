frappe.ui.form.on("Sales Order", {
    before_save: function (frm) {
        frm.trigger('cal_rate_qty')
        frm.doc.items.forEach(function (d) {
            if (!d.item_code) {
                frappe.throw("Please Select the item")
            }

            frappe.call({
                method: 'chemical.api.get_customer_ref_code',
                args: {
                    'item_code': d.item_code,
                    'customer': frm.doc.customer,
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(d.doctype, d.name, 'item_name', r.message);
                    }
                }
            })
        });
        frm.refresh_field('items');
    },
    
    validate: function(frm) {
        frm.doc.items.forEach(function (d) {
			frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock',function(r){
				if(r.maintain_as_is_stock){
                    if (!d.concentration) {
                        frappe.throw("Please add concentration for Item " + d.item_code)
                    }
                    if (d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                    }
                    if (d.price){
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));     
                    }
                }
				else{
                    if (d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                    }
                    if (d.price){
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                    }
				}
			})
        });
        frm.trigger("cal_total_quantity");
    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
		frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
			if(r.maintain_as_is_stock){
                if (!d.concentration) {
                    frappe.throw("Please add concentration for Item " + d.item_code)
                }
                if (d.quantity){
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                }
                if (d.price){
                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));     
                }
            }
            else{
                if (d.quantity){
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                }
                if (d.price){
                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                }
            }
		})
    },
    
    cal_total_quantity: function (frm) {
		let total_quantity = 0.0;
		
		frm.doc.items.forEach(function (d) {
			total_quantity += flt(d.quantity);
		});
		frm.set_value("total_quantity", total_quantity);
	},
    
    
});

cur_frm.fields_dict.items.grid.get_field("outward_sample").get_query = function(doc,cdt,cdn) {
    let d = locals[cdt][cdn];
    if(!d.item_code){
        frappe.throw(__("Please select Item Code first."))
    }
	return {
		filters: {
            'docstatus':1,
            "link_to":'Customer',
            "product_name": d.item_code,
            "party":doc.customer,
            
		}
	}
};

frappe.ui.form.on("Sales Order Item", {
    item_code: function(frm,cdt,cdn) {
        let d = locals[cdt][cdn];
        frappe.model.set_value(d.doctype, d.name, 'outward_sample', "");
		// frm.set_value('outward_sample',"")
		// refresh_field('items');
    },
    quantity: function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm,cdt,cdn)
    },
    price:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm,cdt,cdn)
    },
    concentration: function(frm, cdt, cdn){
        frm.events.cal_rate_qty(frm,cdt,cdn)
    }
});


