// this.frm.add_fetch('batch_no', 'packaging_material', 'packaging_material');
// this.frm.add_fetch('batch_no', 'packing_size', 'packing_size');
// this.frm.add_fetch('batch_no', 'sample_ref_no', 'lot_no');
// this.frm.add_fetch('batch_no', 'batch_yield', 'batch_yield');
// this.frm.add_fetch('batch_no', 'concentration', 'concentration');

/* cur_frm.fields_dict.supplier_transporter.get_query = function(doc) {
	return {
		filters: {
			"supplier_type": "Transporter"
		}
	}
}; */
cur_frm.fields_dict.set_warehouse.get_query = function (doc) {
	return {
		filters: {
			"company": doc.company,
            "is_group":0,
		}
	}
};
cur_frm.fields_dict.items.grid.get_field("warehouse").get_query = function (doc) {
	return {
		filters: {
			"company": doc.company,
            "is_group":0,
		}
	}
};
cur_frm.fields_dict.taxes_and_charges.get_query = function (doc) {
	return {
		filters: {
			"company": doc.company,
		}
	}
};
/* Overide Stock Ledger View Button */
erpnext.accounts.SalesInvoiceController = erpnext.accounts.SalesInvoiceController.extend({
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
    payment_terms_template: function() {
		var me = this;
        const doc = me.frm.doc;
		if(doc.payment_terms_template && doc.doctype !== 'Delivery Note') {
            if (frappe.meta.get_docfield("Sales Invoice", "bl_date") || frappe.meta.get_docfield("Sales Invoice", "shipping_bill_date")){
                var posting_date = doc.bl_date || doc.shipping_bill_date || doc.posting_date
            }
            else{
                var posting_date =  doc.posting_date || doc.transaction_date;
            }
			frappe.call({
				method: "erpnext.controllers.accounts_controller.get_payment_terms",
				args: {
					terms_template: doc.payment_terms_template,
					posting_date: posting_date,
					grand_total: doc.rounded_total || doc.grand_total,
					bill_date: doc.bill_date
				},
				callback: function(r) {
					if(r.message && !r.exc) {
						me.frm.set_value("payment_schedule", r.message);
					}
				}
			})
		}
    },
    // posting_date: function() {
	// 	var me = this;
	// 	if (this.frm.doc.posting_date) {
	// 		if (frappe.meta.get_docfield("Sales Invoice", "bl_date") || frappe.meta.get_docfield("Sales Invoice", "shipping_bill_date")){
    //             var posting_date = this.frm.doc.bl_date || this.frm.doc.shipping_bill_date
    //         }
    //         else{
    //             var posting_date =  this.frm.posting_date || this.frm.doc.transaction_date;
    //         }
	// 		if ((this.frm.doc.doctype == "Sales Invoice" && this.frm.doc.customer) ||
	// 			(this.frm.doc.doctype == "Purchase Invoice" && this.frm.doc.supplier)) {
	// 			return frappe.call({
	// 				method: "erpnext.accounts.party.get_due_date",
	// 				args: {
	// 					"posting_date":posting_date,
	// 					"party_type": me.frm.doc.doctype == "Sales Invoice" ? "Customer" : "Supplier",
	// 					"bill_date": me.frm.doc.bill_date,
	// 					"party": me.frm.doc.doctype == "Sales Invoice" ? me.frm.doc.customer : me.frm.doc.supplier,
	// 					"company": me.frm.doc.company
	// 				},
	// 				callback: function(r, rt) {
	// 					if(r.message) {
	// 						me.frm.doc.due_date = r.message;
    //                         refresh_field("due_date");
    //                         console.log(r.message)
	// 						frappe.ui.form.trigger(me.frm.doc.doctype, "currency");
	// 						me.recalculate_terms();
	// 					}
	// 				}
	// 			})
	// 		} else {
	// 			frappe.ui.form.trigger(me.frm.doc.doctype, "currency");
	// 		}
	// 	}
    // },
    // recalculate_terms: function() {
	// 	const doc = this.frm.doc;
	// 	if (doc.payment_terms_template) {
	// 		this.payment_terms_template();
	// 	} else if (doc.payment_schedule) {
	// 		const me = this;
	// 		doc.payment_schedule.forEach(
	// 			function(term) {
	// 				if (term.payment_term) {
	// 					me.payment_term(doc, term.doctype, term.name);
	// 				} else {
	// 					frappe.model.set_value(
	// 						term.doctype, term.name, 'due_date',
	// 						doc.posting_date || doc.transaction_date
	// 					);
	// 				}
	// 			}
	// 		);
	// 	}
	// },

    set_batch_number: function(cdt, cdn) {
		const doc = frappe.get_doc(cdt, cdn);
		if (doc && doc.has_batch_no && doc.warehouse && !doc.batch_no) {
			this._set_batch_number(doc);
		}
	},

	_set_batch_number: function(doc) {
		let args = {'item_code': doc.item_code, 'warehouse': doc.warehouse, 'qty': flt(doc.qty) * flt(doc.conversion_factor)};
		if (doc.has_serial_no && doc.serial_no) {
			args['serial_no'] = doc.serial_no
		}

		return frappe.call({
			method: 'erpnext.stock.doctype.batch.batch.get_batch_no',
			args: args,
			callback: function(r) {
				if(r.message) {
					frappe.model.set_value(doc.doctype, doc.name, 'batch_no', r.message);
				} else {
				    frappe.model.set_value(doc.doctype, doc.name, 'batch_no', r.message);
				}
			}
		});
	},
})

$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({ frm: cur_frm }));


// Add searchfield to Item query
this.frm.cscript.onload = function (frm) {
    this.frm.set_query("item_code", "items", function () {
        return {
            query: "chemical.query.new_item_query",
            filters: {
                'is_sales_item': 1
            }
        }
    });
    this.frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (!d.item_code) {
            frappe.throw(__("Please enter Item Code to get batch no"));
        }
        else {
            if (d.item_group == "Finished Products"){
                return {
                    query: "chemical.batch_valuation.get_batch_no",
                    filters: {
                        'item_code': d.item_code,
                        'warehouse': d.warehouse,
                    }
                }
            } else {
                return {
                    query: "chemical.query.get_batch_no",
                    filters: {
                        'item_code': d.item_code,
                        'warehouse': d.warehouse
                    }
                }
            }
        }
    });
}

frappe.ui.form.on("Sales Invoice", {
    before_save: function (frm) {
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
                        //frappe.model.set_value(d.doctype, d.name, 'description', r.message);
                    }
                }
            })
        })
    },
    validate: function(frm) {
        frm.doc.items.forEach(function (d) {
            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                if (r.maintain_as_is_stock){
                    if(!d.concentration){
                        frappe.throw("Please add concentration for Item " + d.item_code)
                    }
                }
                if (d.packing_size && d.no_of_packages) {
                    if(frm.doc.is_return == 1){
                        frappe.model.set_value(d.doctype, d.name, 'no_of_packages', -Math.abs(d.no_of_packages));
                    }
                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                    if (r.maintain_as_is_stock) {
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                        if (d.price) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                        }
                    }
                    else {
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                        if (d.price) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                        }
                    }
                }
                else {
                    if (r.maintain_as_is_stock) {
                        if(d.quantity){
                            frappe.model.set_value(d.doctype, d.name, 'qty', d.quantity * 100 / d.concentration);
                        }
                        if (!d.quantity && d.qty){
                            frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                        }
                        if (d.price) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                        }
                    }
                    else {
                        if(d.quantity){
                            frappe.model.set_value(d.doctype, d.name, 'qty', d.quantity);
                        }
                        if(!d.quantity && d.qty){
                            frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                        }
                        if (d.price) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                        }
                    }
                }
			})
        });
        frm.trigger("cal_total_quantity");
    },
    cal_igst_amount: function (frm) {
        let total_igst = 0.0;
        if (frm.doc.currency != "INR") {    
            frm.doc.items.forEach(function (d) {
                if (d.item_tax_template){
                    frappe.db.get_value("Item Tax Template", d.item_tax_template, "gst_rate",function(r){
                        frappe.model.set_value(d.doctype, d.name, 'igst_amount', d.base_amount * parseInt(r.gst_rate) / 100);
                    })
                }
                else if(frm.doc.taxes_and_charges){
                    // console.log(d.igst_amount)
                    frappe.db.get_value("Sales Taxes and Charges Template", frm.doc.taxes_and_charges, "gst_rate", function(r){
                        frappe.model.set_value(d.doctype, d.name, 'igst_amount', d.base_amount * parseInt(r.gst_rate) / 100);
                        // console.log(d.igst_amount)
                    })
                }
                else{
                    frappe.model.set_value(d.doctype, d.name, 'igst_amount', 0.0);
                }
                total_igst += flt(d.igst_amount);
            });
            frm.set_value('total_igst_amount', total_igst);
        }
    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
            if (d.packing_size && d.no_of_packages) {
                if(frm.doc.is_return == 1){
                    frappe.model.set_value(d.doctype, d.name, 'no_of_packages', -Math.abs(d.no_of_packages));
                }
                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                if (r.maintain_as_is_stock) {
                    if(d.quantity != (d.qty * d.concentration / 100)){
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                    }
                    if (d.price) {
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                    }
                }
                else {
                    frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                    if (d.price) {
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                    }
                }
            }
            else {
                if (r.maintain_as_is_stock) {
                    if(d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', d.quantity * 100 / d.concentration);
                    }
                    if (!d.quantity && d.qty){
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                    }
                    if (d.price) {
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
                    }
                }
                else {
                    if(d.quantity){
                        frappe.model.set_value(d.doctype, d.name, 'qty', d.quantity);
                    }
                    if(!d.quantity && d.qty){
                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                    }
                    if (d.price) {
                        frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
                    }
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

    company: function (frm) {
        if (frm.doc.company) {
            frappe.db.get_value("Company", frm.doc.company, 'cost_center', function (r) {
                frm.doc.items.forEach(function (d) {
                    frappe.model.set_value(d.doctype, d.name, 'cost_center', r.cost_center)
                });
            });
        }
    },
    taxes_and_charges: function (frm, cdt, cdn) {
        frm.trigger('cal_igst_amount');
    },
});
frappe.ui.form.on("Sales Invoice Item", {
    item_code: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if(d.batch_no){

            setTimeout(function () {
                frappe.db.get_value("Batch", d.batch_no, ['packaging_material', 'packing_size', 'lot_no', 'batch_yield', 'concentration'], function (r) {
                    frappe.model.set_value(cdt, cdn, 'packaging_material', r.packaging_material);
                    frappe.model.set_value(cdt, cdn, 'packing_size', r.packing_size);
                    frappe.model.set_value(cdt, cdn, 'lot_no', r.lot_no);
                    frappe.model.set_value(cdt, cdn, 'batch_yield', r.batch_yield);
                    frappe.model.set_value(cdt, cdn, 'concentration', r.concentration);
                })
            }, 1000)
        }
    },
    // price:function(frm,cdt,cdn){
    //     frm.events.cal_rate_qty(frm,cdt,cdn)
    // },
    // concentration: function(frm, cdt, cdn){
    //     frm.events.cal_rate_qty(frm,cdt,cdn)
    // },
    // packing_size: function (frm, cdt, cdn) {
    //     frm.events.cal_rate_qty(frm, cdt, cdn)
    // },
    no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },

    batch_no: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (d.batch_no){
            frappe.db.get_value("Batch", d.batch_no, ['packaging_material', 'packing_size', 'lot_no', 'batch_yield', 'concentration'], function (r) {
                frappe.model.set_value(cdt, cdn, 'packaging_material', r.packaging_material);
                frappe.model.set_value(cdt, cdn, 'packing_size', r.packing_size);
                frappe.model.set_value(cdt, cdn, 'lot_no', r.lot_no);
                frappe.model.set_value(cdt, cdn, 'batch_yield', r.batch_yield);
                frappe.model.set_value(cdt, cdn, 'concentration', r.concentration);
            });
            frm.events.cal_rate_qty(frm,cdt,cdn)
        }
    },
    item_tax_template: function (frm, cdt, cdn) {
        frm.trigger('cal_igst_amount');
    }
});

erpnext.selling.SellingController = erpnext.TransactionController.extend({
    
})
