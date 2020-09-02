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
            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                if (!d.supplier_qty) {
                    frappe.model.set_value(d.doctype, d.name, 'supplier_qty', d.qty)
                }
                if (d.packing_size && d.no_of_packages) {
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                    frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.packing_size * d.no_of_packages));
                    if (r.maintain_as_is_stock) {
                        if (!d.supplier_concentration) {
                            frappe.throw("Please add concentration for Item " + d.item_code)
                        }
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty * d.supplier_concentration / 100));
                    }
                    else {
                        frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                    }
                }
                else {
                    if (r.maintain_as_is_stock) {
                        if (!d.supplier_concentration) {
                            frappe.throw("Please add concentration for Item " + d.item_code)
                        }
                        if (d.quantity) {
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((d.quantity * 100.0) / d.concentration));
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty * d.supplier_concentration / 100));
                        }
                    }
                    else {
                        if (d.quantity) {
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                        }
                       
                    }
                }
                frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.supplier_quantity * d.price))
                frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_amount / d.qty))
                frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.supplier_amount) - (d.quantity * d.price))
            });
        });
        
    },
    before_save: function (frm) {
        frm.trigger("cal_total");
    },
    cal_total: function(frm){
        let total_quantity = 0;
        let total_supplier_qty = 0;
        let total_supplier_quantity = 0;
        let total_packages = 0;

		frm.doc.items.forEach(function (d) {	
            total_quantity += flt(d.quantity);  
            total_supplier_qty += flt(d.supplier_qty);
            total_supplier_quantity += flt(d.supplier_quantity);
            total_packages += flt(d.no_of_packages);

		});
		frm.set_value("total_quantity", total_quantity);
		frm.set_value("total_supplier_qty", total_supplier_qty);
		frm.set_value("total_supplier_quantity", total_supplier_quantity);
		frm.set_value("total_packages", total_packages);

    },
    
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
            if (!d.supplier_qty) {
                frappe.model.set_value(d.doctype, d.name, 'supplier_qty', d.qty)
            }
            if (d.packing_size && d.no_of_packages) {
                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.packing_size * d.no_of_packages));
                if (r.maintain_as_is_stock) {
                    
                    frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                    frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty * d.supplier_concentration / 100));
                }
                else {
                    frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                    frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                }
            }
            else {
                if (r.maintain_as_is_stock) {
                   
                    if (d.quantity) {
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((d.quantity * 100.0) / d.concentration));
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty * d.supplier_concentration / 100));
                    }
                }
                else {
                    if (d.quantity) {
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                    }

                }
            }
            frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.supplier_quantity * d.price))
            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_amount / d.qty))
            frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.supplier_amount) - (d.quantity * d.price))
        });
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
    },
    packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
});