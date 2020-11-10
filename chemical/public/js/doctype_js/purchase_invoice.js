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

erpnext.accounts.PurchaseInvoice = erpnext.accounts.PurchaseInvoice.extend({
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

$.extend(cur_frm.cscript, new erpnext.accounts.PurchaseInvoice({ frm: cur_frm }));

frappe.ui.form.on("Purchase Invoice", {
    validate: function(frm) {  
        frm.doc.items.forEach(function (d) {     
            var packing_size = 0;
            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")){
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")){
                            packing_size = (d.receive_packing_size - d.tare_weight)
                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                        }
                    }
                    else{
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")){
                            packing_size = d.receive_packing_size
                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                        }                        
                    }
                }
                else{
                    if (d.packing_size && d.no_of_packages){
                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                    }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                        frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
                 }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")){
                        frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
                 }
                 if(!d.supplier_qty){
                     frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier Qty")
                 }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size")){
                        frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                        frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'packing_size',packing_size);
                        frappe.model.set_value(d.doctype, d.name, 'no_of_packages',d.receive_no_of_packages);
                    }
                }

                if(r.maintain_as_is_stock){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty) * d.received_concentration / 100);
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                        if(!d.supplier_concentration){
                            frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier concentration")
                        }
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty) * d.supplier_concentration / 100);
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty) * d.accepted_concentration / 100);
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'concentration',d.accepted_concentration || d.received_concentration);
                    }
                    if (!d.qty){
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                            frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                        }
                        else{
                            frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                        }
                    }

                    if (!d.concentration){
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                            frappe.throw(d.doctype + " Row: "+ d.idx +" Please add received or accepted concentration")
                        }
                        else{
                            frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add concentration")
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")){
                        frappe.model.set_value(d.doctype, d.name, 'quantity',d.accepted_quantity || d.receive_quantity);
                    }

                    else{
                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty)*flt(d.concentration)/100);
                    }
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                        frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.quantity) * flt(d.price) / flt(d.qty));
                    }
                }
                else{
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty));
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty));
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty));
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                        frappe.model.set_value(d.doctype, d.name, 'concentration',flt(d.accepted_concentration) || flt(d.received_concentration));
                    }

                    if (!d.qty){
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                            frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                        }
                        else{
                            frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")){
                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.accepted_quantity) || flt(d.receive_quantity));
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty));
                    }
                    frappe.model.set_value(d.doctype, d.name, 'rate',d.price);
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")){
                    frappe.model.set_value(d.doctype, d.name, 'short_quantity',flt(d.quantity) - flt(d.supplier_quantity));
                    if(d.short_quantity){
                        frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                    }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "amount_difference")){
                    frappe.model.set_value(d.doctype, d.name, 'amount_difference',flt(d.price) * flt(d.short_quantity));
                }

            });
        });

    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        var packing_size = 0;
        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")){
                        packing_size = (d.receive_packing_size - d.tare_weight)
                        frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                    }
                }

                else{
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")){
                        packing_size = d.receive_packing_size
                        frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                    }                        
                }
            }
            
            else{
                if (d.packing_size && d.no_of_packages){
                    frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                    frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                }
            }

            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                    frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
             }
            }

            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")){
                    frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
             }

             if(!d.supplier_qty){
                 //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier Qty")
             }
            }

            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size")){
                    frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                    frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                }

                else{
                    frappe.model.set_value(d.doctype, d.name, 'packing_size',packing_size);
                    frappe.model.set_value(d.doctype, d.name, 'no_of_packages',d.receive_no_of_packages);
                }
            }

            if(r.maintain_as_is_stock){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty) * d.received_concentration / 100);
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                    if(!d.supplier_concentration){
                        //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier concentration")
                    }
                    frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty) * d.supplier_concentration / 100);
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty) * d.accepted_concentration / 100);
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'concentration',d.accepted_concentration || d.received_concentration);
                }
                if (!d.qty){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                    }
                    else{
                       // frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                    }
                }

                if (!d.concentration){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                        //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add received or accepted concentration")
                    }
                    else{
                       // frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add concentration")
                    }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")){
                    frappe.model.set_value(d.doctype, d.name, 'quantity',d.accepted_quantity || d.receive_quantity);
                }

                else{
                    frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty)*flt(d.concentration)/100);
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                    frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.quantity) * flt(d.price) / flt(d.qty));
                }
            }
            else{
                if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty));
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty));
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty));
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")){
                    frappe.model.set_value(d.doctype, d.name, 'concentration',flt(d.accepted_concentration) || flt(d.received_concentration));
                }

                if (!d.qty){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                       // frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                    }
                    else{
                      //  frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                    }
                }

                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")){
                    frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.accepted_quantity) || flt(d.receive_quantity));
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty));
                }
                frappe.model.set_value(d.doctype, d.name, 'rate',d.price);
            }

            if (frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")){
                frappe.model.set_value(d.doctype, d.name, 'short_quantity',flt(d.quantity) - flt(d.supplier_quantity));
                if(d.short_quantity){
                    frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                }
            }
            
            if (frappe.meta.get_docfield("Purchase Invoice Item", "amount_difference")){
                frappe.model.set_value(d.doctype, d.name, 'amount_difference',flt(d.price) * flt(d.short_quantity));
            }

        });
	},
});
frappe.ui.form.on("Purchase Invoice Item", {
	price: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    receive_packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    receive_no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    received_concentration: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    concentration: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    tare_weight: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_concentration: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_concentration: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
});
