if (frappe.get_route()[3] == "Item-wise Price List Rate") {
    var r= $('<input type="button" value="new button"/>');
        $("button.add-groupby").after(r);
        $('active-tag-filters .button.add-filter').after($('<input type="button" value="test">'));
    console.log($(".tag-groupby-area"))
    console.log(" first")
   
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