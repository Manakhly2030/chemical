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
            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                    if (!d.concentration && d.received_concentration && !d.accepted_concentration){
                        d.concentration = d.received_concentration
                        }
                    if (d.accepted_concentration){
                        d.concentration = d.accepted_concentration
                        }
                }
                if(r.maintain_as_is_stock){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                        if (!d.supplier_concentration){
                            frappe.throw(d.doctype+ "Row: "+ d.idx + "Please add supplier concentration")
                        }
                    }
                    if(!d.concentration){
                        frappe.throw(d.doctype+ "Row: "+ d.idx + "Please add received or accepted concentration")
                    }
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                    frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) *  flt(d.accepted_no_of_packages))
                }

                if (d.packing_size && d.no_of_packages) {
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")){
                      if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        frappe.model.set_value(d.doctype, d.name, 'receive_qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                        }
                      else{
                          frappe.model.set_value(d.doctype, d.name, 'qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                          frappe.model.set_value(d.doctype, d.name, 'received_qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                        }
                    }
                    else{
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt(d.packing_size) * flt(d.no_of_packages));
                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.packing_size) * flt(d.no_of_packages));
                            }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size) * flt(d.no_of_packages));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.packing_size) * flt(d.no_of_packages));
                            }
                    }
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        if (!d.accepted_qty){
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.receive_qty));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.receive_qty));
                        }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.accepted_qty));                            
                        }
                    }
                    if (r.maintain_as_is_stock) {
                        frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty) * d.concentration / 100);
                    }
                    else {
                        frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                    }
                }
                //else of this: if (d.packing_size && d.no_of_packages)
                else {
                    if (r.maintain_as_is_stock) {
                        if (d.quantity) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                                frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt((flt(d.quantity) * 100.0) / d.concentration));    
                            }
                            else{
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                            }
                            }
                    }
                    else {
                        if (d.quantity) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt(d.quantity));
                                frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.quantity));    
                            }
                            else{
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                            }
                        }
                    }
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        if (!d.accepted_qty){
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.receive_qty));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.receive_qty));
                        }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.accepted_qty));                            
                        }
                    }
                }
                if(!d.qty){
                    frappe.throw("Row: "+ d.idx + "Please Input Received Qty.")
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")){
                        frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages))
                        if(!d.supplier_qty){
                            frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.qty))
                        }
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                            if(r.maintain_as_is_stock){
                                frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', (flt(d.supplier_qty) * flt(d.supplier_concentration))/100)
                            }
                            else{
                                frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty))
                            }
                        }
                    }
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_amount")){
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                        if (!d.supplier_quantity){
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.quantity))
                        }
                        frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.supplier_quantity) * flt(d.price))
                        frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.supplier_amount) -(flt(d.quantity) *  flt(d.price)))
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.quantity) *  flt(d.price))
                    }
    
                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_amount) /  flt(d.qty))
                }
                else{
                    let concentration = d.concentration || 100
                    frappe.model.set_value(d.doctype, d.name, 'rate', (flt(d.price) *  flt(concentration))/100)
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                    //frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) *  flt(d.accepted_no_of_packages))
                    if(r.maintain_as_is_stock){
                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', (flt(d.accepted_qty) *  flt(d.accepted_concentration))/100)                
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty))                
                    }
                }
                else if(frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity")){
                    if (!d.accepted_quantity && frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")){
                        frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity))                      
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.accepted_quantity) - flt(d.supplier_quantity)) 
                    }
                }
                else if(frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")) {
                    frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity))                 
                }
            });
        }); 
    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
            if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")){
                if (!d.concentration && d.received_concentration && !d.accepted_concentration){
                    d.concentration = d.received_concentration
                    }
                if (d.accepted_concentration){
                    d.concentration = d.accepted_concentration
                    }
            }
            if(r.maintain_as_is_stock){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")){
                    if (!d.supplier_concentration){
                        frappe.throw(d.doctype+ "Row: "+ d.idx + "Please add supplier concentration")
                    }
                }
                if(!d.concentration){
                    frappe.throw(d.doctype+ "Row: "+ d.idx + "Please add received or accepted concentration")
                }
            }
            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) *  flt(d.accepted_no_of_packages))
            }

            if (d.packing_size && d.no_of_packages) {
                if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")){
                  if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    frappe.model.set_value(d.doctype, d.name, 'receive_qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                    frappe.model.set_value(d.doctype, d.name, 'receive_quantity', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                    }
                  else{
                      frappe.model.set_value(d.doctype, d.name, 'qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                      frappe.model.set_value(d.doctype, d.name, 'received_qty', (flt(d.packing_size) - flt(d.tare_weight)) * flt(d.no_of_packages));
                    }
                }
                else{
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                        frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt(d.packing_size) * flt(d.no_of_packages));
                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.packing_size) * flt(d.no_of_packages));
                        }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size) * flt(d.no_of_packages));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.packing_size) * flt(d.no_of_packages));
                        }
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    if (!d.accepted_qty){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.receive_qty));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.receive_qty));
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.accepted_qty));                            
                    }
                }
                if (r.maintain_as_is_stock) {
                    frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty) * d.concentration / 100);
                }
                else {
                    frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                }
            }
            //else of this: if (d.packing_size && d.no_of_packages)
            else {
                if (r.maintain_as_is_stock) {
                    if (d.quantity) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt((flt(d.quantity) * 100.0) / d.concentration));    
                        }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt((flt(d.quantity) * 100.0) / d.concentration));
                        }
                        }
                }
                else {
                    if (d.quantity) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', flt(d.quantity));
                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.quantity));    
                        }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                            frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.quantity));
                        }
                    }
                }
                if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")){
                    if (!d.accepted_qty){
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.receive_qty));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.receive_qty));
                    }
                    else{
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty));
                        frappe.model.set_value(d.doctype, d.name, 'received_qty', flt(d.accepted_qty));                            
                    }
                }
            }
            if(!d.qty){
                frappe.throw("Row: "+ d.idx + "Please Input Received Qty.")
            }
            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")){
                    frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages))
                    if(!d.supplier_qty){
                        frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.qty))
                    }
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                        if(r.maintain_as_is_stock){
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', (flt(d.supplier_qty) * flt(d.supplier_concentration))/100)
                        }
                        else{
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty))
                        }
                    }
                }
            }
            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_amount")){
                if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")){
                    if (!d.supplier_quantity){
                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.quantity))
                    }
                    frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.supplier_quantity) * flt(d.price))
                    frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.supplier_amount) -(flt(d.quantity) *  flt(d.price)))
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'supplier_amount', flt(d.quantity) *  flt(d.price))
                }

                frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_amount) /  flt(d.qty))
            }
            else{
                let concentration = d.concentration || 100
                frappe.model.set_value(d.doctype, d.name, 'rate', (flt(d.price) *  flt(concentration))/100)
            }
            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")){
                //frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) *  flt(d.accepted_no_of_packages))
                if(r.maintain_as_is_stock){
                    frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', (flt(d.accepted_qty) *  flt(d.accepted_concentration))/100)                
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty))                
                }
            }
            else if(frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity")){
                if (!d.accepted_quantity && frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")){
                    frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity))                      
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.accepted_quantity) - flt(d.supplier_quantity)) 
                }
            }
            else if(frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")) {
                frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity))                 
            }
        });
	},
});
frappe.ui.form.on("Purchase Invoice Item", {
	price: function (frm, cdt, cdn) {
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
});
