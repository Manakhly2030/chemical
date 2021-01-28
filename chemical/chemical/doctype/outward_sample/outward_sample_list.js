frappe.listview_settings['Outward Sample'] = {
    add_fields: ["status"],
	get_indicator: function (doc) {
        if (doc.status === "Approved"){
            return [__("Approved"), "blue", "status,=,Approved"];
        }
        else if(doc.status === "Pending"){
            return [__("Pending"), "orange", "status,=,Pending"];
        }
        else if(doc.status === "Fail"){
            return [__("Fail"), "red", "status,=,Fail"];
        }
		
    }
}
