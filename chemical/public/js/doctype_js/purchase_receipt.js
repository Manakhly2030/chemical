erpnext.stock.PurchaseReceiptController = erpnext.stock.PurchaseReceiptController.extend({
    show_stock_ledger: function () {
        var me = this;
        if (this.frm.doc.docstatus === 1) {
            cur_frm.add_custom_button(__("Stock Ledger Chemical"), function () {
                frappe.route_options = {
                    voucher_no: me.frm.doc.name,
                    from_date: me.frm.doc.posting_date,
                    to_date: me.frm.doc.posting_date,
                    company: me.frm.doc.company
                };
                frappe.set_route("query-report", "Stock Ledger Chemical");
            }, __("View"));
        }

    },
})

$.extend(cur_frm.cscript, new erpnext.stock.PurchaseReceiptController({ frm: cur_frm }));

frappe.ui.form.on("Purchase Receipt", {
    validate: function(frm) {
        frm.doc.items.forEach(function (d) {
            
			frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock',function(r){
				if (r.maintain_as_is_stock) {
                    if (!d.concentration) {
                        frappe.throw("Please add concentration for Item " + d.item_code)
                    }
                    if (d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((d.quantity * 100.0) / d.concentration));
                    }
                    if (d.price){
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                    }
                }
                else {
                    if (d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                    }
                    if (d.price){
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                    }
                }
			})
        });
    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
		frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
			if (r.maintain_as_is_stock) {
                if (!d.concentration) {
                    frappe.throw("Please add concentration for Item " + d.item_code)
                }
                if (d.quantity){
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                    frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((d.quantity * 100.0) / d.concentration));
                }
                if (d.price){
                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                }
			}
			else {
                if (d.quantity){
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                    frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                }
                if (d.price){
                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                }
			}
		})
	},
    
});

frappe.ui.form.on("Purchase Receipt Item", {
	quantity: function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm,cdt,cdn)
    },
    price:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm,cdt,cdn)
    },  
    concentration: function(frm, cdt, cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    }
});