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
    company: function (frm) {
        if (frm.doc.company) {
            frappe.db.get_value("Company", frm.doc.company, 'cost_center', function (r) {
                frm.doc.items.forEach(function (d) {
                    frappe.model.set_value(d.doctype, d.name, 'cost_center', r.cost_center)
                });
            });
        }
    }
    
});
frappe.ui.form.on("Sales Invoice Item", {
    item_code: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        setTimeout(function () {
            frappe.db.get_value("Batch", d.batch_no, ['packaging_material', 'packing_size', 'lot_no', 'batch_yield', 'concentration'], function (r) {
                frappe.model.set_value(cdt, cdn, 'packaging_material', r.packaging_material);
                frappe.model.set_value(cdt, cdn, 'packing_size', r.packing_size);
                frappe.model.set_value(cdt, cdn, 'lot_no', r.lot_no);
                frappe.model.set_value(cdt, cdn, 'batch_yield', r.batch_yield);
                frappe.model.set_value(cdt, cdn, 'concentration', r.concentration);
            })
        }, 1000)
    },

    batch_no: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        frappe.db.get_value("Batch", d.batch_no, ['packaging_material', 'packing_size', 'lot_no', 'batch_yield', 'concentration'], function (r) {
            frappe.model.set_value(cdt, cdn, 'packaging_material', r.packaging_material);
            frappe.model.set_value(cdt, cdn, 'packing_size', r.packing_size);
            frappe.model.set_value(cdt, cdn, 'lot_no', r.lot_no);
            frappe.model.set_value(cdt, cdn, 'batch_yield', r.batch_yield);
            frappe.model.set_value(cdt, cdn, 'concentration', r.concentration);
        });
    }
});