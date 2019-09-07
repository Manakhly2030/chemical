frappe.ui.form.on("Customer", {
	onload_post_render: function(frm){
		if(frm.doc.alias && !frm.doc.__islocal && frm.doc.name != frm.doc.alias){
			frappe.call({
				method: "frappe.client.rename_doc",
				args: {
					'doctype': frm.doc.doctype,
					'old_name': frm.doc.name,
					'new_name': frm.doc.alias
				},
				callback: function(r){
					if(r.message){
						frappe.set_route('Form', 'Customer', r.message)
					}
				}
			})
		}
	},
	before_save: function(frm){
		if((frm.doc.accounts == undefined || !frm.doc.accounts.length) && frm.doc.default_currency != undefined){
            if (frm.doc.default_currency == 'USD') {
                let accounts = frm.add_child('accounts');
                accounts.company = frappe.defaults.get_user_default("Company");
                frappe.db.get_value("Company", accounts.company, 'abbr', function (r) {
                    accounts.account = 'Debtor USD - ' + r.abbr;
                });
                }
            else if(frm.doc.default_currency == 'EUR'){
                let accounts = frm.add_child('accounts');
                accounts.company = frappe.defaults.get_user_default("Company");
                frappe.db.get_value("Company", accounts.company, 'abbr', function (r) {
                    accounts.account = 'Debtors EUR - ' + r.abbr;
                });
            }
			frm.refresh_field('accounts');
		} 
	}

});