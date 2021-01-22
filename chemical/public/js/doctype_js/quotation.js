frappe.ui.form.on("Quotation", {
    onload: function(frm){
        frm.doc.items.forEach(function(d){
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
                        r.message.forEach(function (lst){
                            frappe.model.with_doc("Outward Sample", lst.name, function(){
                                let doc_outward = frappe.get_doc("Outward Sample", lst.name)
                                frm.refresh_field("items")
                                let d = frm.add_child("items");
                                d.item_code = doc_outward.product_name;
                                d.item_name = doc_outward.product_name;
                                d.outward_sample = doc_outward.name;
                                d.rmc = doc_outward.per_unit_price;
                                d.sample_ref_no = doc_outward.ref_no;
                                d.base_cost = doc_outward.per_unit_price;
                                var item = d.item_code
                                frappe.model.set_value(d.doctype,d.name,"item_code","")
                                frappe.model.set_value(d.doctype,d.name,"item_code",item)
                                frm.refresh_field("items")
                            })
                        })
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
                        r.message.forEach(function (lst){
                            frappe.model.with_doc("Outward Sample", lst.name, function(){
                                let doc_outward = frappe.get_doc("Outward Sample", lst.name)
                                frm.refresh_field("items")
                                let d = frm.add_child("items");
                                d.item_code = doc_outward.product_name;
                                d.item_name = doc_outward.product_name;
                                d.outward_sample = doc_outward.name;
                                d.rmc = doc_outward.per_unit_price;
                                d.sample_ref_no = doc_outward.ref_no;
                                d.base_cost = doc_outward.per_unit_price;
                                var item = d.item_code
                                frappe.model.set_value(d.doctype,d.name,"item_code","")
                                frappe.model.set_value(d.doctype,d.name,"item_code",item)
                                frm.refresh_field("items")
                            })
                        })
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