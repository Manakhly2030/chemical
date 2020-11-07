if (frappe.get_route()[3] == "Item-wise Price List Rate") {
    console.log("called first")
    frappe.cur_page.add_custom_button("button", function() {
        console.log("called in button")
    })  
}

// frappe.query_reports["Item-wise Price List Rate"] = {
//     onload: function(report) {
//     report.page.add_inner_button(__("Test"), function() {
//         frappe.msgprint("Test");
//     });
// }
// frappe.views.ReportView["Item-wise Price List Rate"] = {
//     onload:function(){
//         console.log("called")
//     }
// }