frappe.ui.form.on("Quotation", {
    onload: function(frm){
        frm.doc.items.forEach(function (d){
            var item = d.item_code
            frappe.model.set_value(d.doctype,d.name,"item_code","")
            frappe.model.set_value(d.doctype,d.name,"item_code",item)
        })
    },
    get_approved: function(frm){
        if(frm.doc.quotation_to=="Customer" && frm.doc.party_name){
            frappe.call({
                method:"chemical.chemical.doc_events.quotation.get_approved_outward_sample_list",
                args:{
                    "party":frm.doc.party_name,
                },
                freeze:true,
                callback: function(r){
                    if(r.message){
                        frm.doc.items = []
                        r.message.forEach(function (item){
                                var d = frm.add_child("items");
                                frappe.model.set_value(d.doctype,d.name,"item_code",item.product_name)
                                frappe.model.set_value(d.doctype,d.name,"outward_sample",item.name)
                                frappe.model.set_value(d.doctype,d.name,"sample_ref_no",item.ref_no)
                                frappe.model.set_value(d.doctype,d.name,"base_cost",item.per_unit_price)
                            })
                            frm.refresh_field("items")
                        }
                }
            })
        }
    },
    get_samples: function(frm){
        if(frm.doc.quotation_to=="Customer" && frm.doc.party_name){
            frappe.call({
                method:"chemical.chemical.doc_events.quotation.get_outward_sample_list",
                args:{
                    "party":frm.doc.party_name,
                },
                freeze:true,
                callback: function(r){
                    if(r.message){
                        frm.doc.items = []
                        r.message.forEach(function (item){
                                var d = frm.add_child("items");
                                frappe.model.set_value(d.doctype,d.name,"item_code",item.product_name)
                                frappe.model.set_value(d.doctype,d.name,"outward_sample",item.name)
                                frappe.model.set_value(d.doctype,d.name,"sample_ref_no",item.ref_no)
                                frappe.model.set_value(d.doctype,d.name,"base_cost",item.per_unit_price)
                            })
                        frm.refresh_field("items")
                        }
                }
            })
        }
    },
    cal_margin: function(frm,cdt,cdn)
    {
        let d = locals[cdt][cdn];
        if (frappe.meta.get_docfield("Quotation Item", "base_cost")){
            if (d.base_cost){
                frappe.model.set_value(d.doctype,d.name,'margin_with_rmc',flt(d.rate - d.base_cost))
            }
        }
    }
});

frappe.ui.form.on("Quotation Item", {
    rate: function(frm,cdt,cdn){
        frm.events.cal_margin(frm,cdt,cdn)
    }
});