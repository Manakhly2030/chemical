cur_frm.fields_dict['item_code'].get_query = function(doc, cdt, cdn) {
	// const doctype = (doc.reference_type == "Stock Entry") ?
	// 	"Stock Entry Detail" : doc.reference_type + " Item";
    if(doc.reference_type == "Stock Entry"){
       var doctype = "Stock Entry Detail"
    }
    else if(doc.reference_type == "Outward Sample"){
        var doctype = "Outward Sample Detail"
    }
    else{
        var doctype = doc.reference_type + " Item";
    }
	if (doc.reference_type && doc.reference_name && doc.reference_type!="Inward Sample") {
		return {
			query: "chemical.query.item_query",
			filters: {
				"from": doctype
			}
		};
	}
}