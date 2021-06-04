// Copyright (c) 2016, FinByz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GST Itemised Purchase Register Chemical"] = {
	"filters": [

	]
};
// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

{% include "chemical/chemical/report/item_wise_purchase_register_chemical/item_wise_purchase_register_chemical.js" %}

frappe.query_reports["GST Itemised Purchase Register Chemical"] = frappe.query_reports["Item-wise Purchase Register Chemical"]

