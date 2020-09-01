
// Add searchfield to Item query
this.frm.cscript.onload = function(frm) {
	this.frm.set_query("item_code", "items", function() {
		return {
			query: "chemical.query.new_item_query",
			filters: {
				'is_sales_item': 1
			}
		}
	});
}

frappe.ui.form.on("Purchase Order", {
    validate: function(frm) {
        frm.doc.items.forEach(function (d) {
			frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock',function(r){
				if(r.maintain_as_is_stock){
					// if (!d.concentration) {
					// 	frappe.throw("Please add concentration for Item " + d.item_code)
					// }
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
		total_quantity = 0;
		$.each(frm.doc.items, function(d) {
			console.log('call')
			total_quantity += flt(d.quantity);
		});
		frm.set_value("total_quantity", total_quantity);
	},
	
    company: function (frm) {
        frappe.call({
            method: "gopinath.api.company_address",
            args: {
                'company': frm.doc.company
            },
            callback: function (r) {
				console.log(r.message)
                if (r.message) {
                    frm.set_value("billing_address", r.message.company_address);
                 }
            }
        })
    },

	cal_rate_qty: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
			if(r.maintain_as_is_stock){
				// if (!d.concentration) {
                //     frappe.throw("Please add concentration for Item " + d.item_code)
                // }
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
    
});

frappe.ui.form.on("Purchase Order Item", {
	quantity: function(frm,cdt,cdn){
		frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    price:function(frm,cdt,cdn){
		frm.events.cal_rate_qty(frm,cdt,cdn)
	},  
    concentration: function(frm, cdt, cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    }
});