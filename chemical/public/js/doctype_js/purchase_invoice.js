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