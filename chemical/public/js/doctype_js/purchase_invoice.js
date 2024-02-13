frappe.ui.form.on("Purchase Invoice", {
    refresh: function(frm) {
        if (frm.doc.docstatus > 0 && frm.doc.update_stock) {
            cur_frm.add_custom_button(__("Stock Ledger Chemical"), function() {
                frappe.route_options = {
                    voucher_no: frm.doc.name,
                    from_date: frm.doc.posting_date,
                    to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
                    company: frm.doc.company,
                    show_cancelled_entries: frm.doc.docstatus === 2,
                    ignore_prepared_report: true
                };
                frappe.set_route("query-report", "Stock Ledger Chemical");
            }, __("View"));
        }
    },
    onload_post_render: function(frm) {
        frm.page.remove_inner_button("Stock Ledger", "View")
    },
    validate: function(frm) {
        frappe.db.get_value("Company", frm.doc.company, 'maintain_as_is_new', function(c) {
            if(!c.maintain_as_is_new) {
                frm.doc.items.forEach(function(d) {
                    var packing_size = 0;
                    frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")) {
                                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")) {
                                    packing_size = (d.receive_packing_size - d.tare_weight)
                                    frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                }
                            } else {
                                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")) {
                                    packing_size = d.receive_packing_size
                                    frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                }
                            }
                        } else {
                            if (d.packing_size && d.no_of_packages) {
                                if (d.qty != d.packing_size * d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                }
                                if (d.received_qty != d.packing_size * d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                }
                            }
                        }
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty")) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")) {
                                frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
                            }
                        }
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")) {
                                frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
                            }
                            if (!d.supplier_qty) {
                                frappe.throw(d.doctype + " Row: " + d.idx + " Please add supplier Qty")
                            }
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size")) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size")) {
                                frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                                frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                            } else {
                                if (d.packing_size != packing_size) {
                                    frappe.model.set_value(d.doctype, d.name, 'packing_size', packing_size);
                                }
                                if (d.no_of_packages != d.receive_no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.receive_no_of_packages);
                                }
                            }
                        }
                        if (r.maintain_as_is_stock) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.receive_qty) * d.received_concentration / 100);
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")) {
                                if (!d.supplier_concentration) {
                                    frappe.throw(d.doctype + " Row: " + d.idx + " Please add supplier concentration")
                                }
                                frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty) * d.supplier_concentration / 100);
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty) * d.accepted_concentration / 100);
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty) || flt(d.receive_qty));
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'concentration', d.accepted_concentration || d.received_concentration);
                            }

                            if (!frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty") && (!d.packing_size || !d.no_of_packages)) {
                                if (d.quantity && d.qty != (flt(d.quantity) * 100.0) / flt(d.concentration)) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', (flt(d.quantity) * 100.0) / flt(d.concentration))
                                }
                            }

                            if (!d.qty) {
                                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                    frappe.throw(d.doctype + " Row: " + d.idx + " Please add Receive Qty or Accepted Qty")
                                } else {
                                    frappe.throw(d.doctype + " Row: " + d.idx + "  Please add Qty")
                                }
                            }
                            if (!d.concentration) {
                                if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                    frappe.throw(d.doctype + " Row: " + d.idx + " Please add received or accepted concentration")
                                } else {
                                    frappe.throw(d.doctype + " Row: " + d.idx + "  Please add concentration")
                                }
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")) {
                                frappe.model.set_value(d.doctype, d.name, 'quantity', d.accepted_quantity || d.receive_quantity);
                            } else {
                                if (d.quantity != flt(d.qty) * flt(d.concentration) / 100) {
                                    frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty) * flt(d.concentration) / 100);
                                }
                            }
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")) {
                                frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                            } else {
                                if (d.rate != flt(d.quantity) * flt(d.price) / flt(d.qty)) {
                                    frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity) * flt(d.price) / flt(d.qty));
                                }
                            }
                        } else {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.receive_qty));
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty));
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty) || flt(d.receive_qty));
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                frappe.model.set_value(d.doctype, d.name, 'concentration', flt(d.accepted_concentration) || flt(d.received_concentration));
                            }

                            if (!frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty") && (!d.packing_size || !d.no_of_packages)) {
                                if (d.quantity && d.qty != d.quantity) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity))
                                }
                            }

                            if (!d.qty) {
                                if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                    frappe.throw(d.doctype + " Row: " + d.idx + " Please add Receive Qty or Accepted Qty")
                                } else {
                                    frappe.throw(d.doctype + " Row: " + d.idx + "  Please add Qty")
                                }
                            }

                            if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")) {
                                frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.accepted_quantity) || flt(d.receive_quantity));
                            } else {
                                if (d.quantity != d.qty) {
                                    frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                                }
                            }
                            if (d.rate != d.price) {
                                frappe.model.set_value(d.doctype, d.name, 'rate', d.price);
                            }
                        }
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")) {
                            frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity));
                            if (d.short_quantity) {
                                frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                            }
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "amount_difference")) {
                            frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.price) * flt(d.short_quantity));
                        }

                    });
                });
            } else {
                frm.doc.items.forEach(function(d) {
                    if(!d.ignore_calculation) {
                        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                            if(r.maintain_as_is_stock){
                                frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                            } else {
                                if (d.packing_size && d.no_of_packages) {
                                    if (d.qty != d.packing_size * d.no_of_packages) {
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                    }
                                    if (d.received_qty != d.packing_size * d.no_of_packages) {
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                            }
                        });
                    } else {
                        if(d.ignore_calculation){
                            if (d.packing_size && d.no_of_packages) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                            }
                        }
                    }
				}); 
            }
        });

    },
    cal_rate_qty: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        var packing_size = 0;
        frappe.db.get_value("Company", frm.doc.company, 'maintain_as_is_new', function(c) {
            if(!c.maintain_as_is_new) {
                frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "tare_weight")) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")) {
                                packing_size = (d.receive_packing_size - d.tare_weight)
                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                            }
                        } else {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_no_of_packages")) {
                                packing_size = d.receive_packing_size
                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                            }
                        }
                    } else {
                        if (d.packing_size && d.no_of_packages) {
                            packing_size = d.packing_size
                            if (d.qty != (d.packing_size * d.no_of_packages)) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                            }
                            if (d.received_qty != (d.packing_size * d.no_of_packages)) {
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                            }
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty")) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "accepted_no_of_packages")) {
                            frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_qty")) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_packing_size") && frappe.meta.get_docfield("Purchase Invoice Item", "supplier_no_of_packages")) {
                            frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
                        }

                        if (!d.supplier_qty) {
                            //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier Qty")
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_packing_size")) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_packing_size")) {
                            frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                            frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                        } else {
                            if (d.packing_size != packing_size) {
                                frappe.model.set_value(d.doctype, d.name, 'packing_size', packing_size);
                            }
                            if (d.no_of_packages != d.receive_no_of_packages) {
                                frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.receive_no_of_packages);
                            }
                        }
                    }

                    if (r.maintain_as_is_stock) {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.receive_qty) * d.received_concentration / 100);
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")) {
                            if (!d.supplier_concentration) {
                                //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier concentration")
                            }
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty) * d.supplier_concentration / 100);
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty) * d.accepted_concentration / 100);
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty) || flt(d.receive_qty));
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'concentration', d.accepted_concentration || d.received_concentration);
                        }

                        if (!frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty") && (!d.packing_size || !d.no_of_packages)) {
                            if (d.quantity) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', (flt(d.quantity) * 100.0) / flt(d.concentration))
                            }
                        }
                        if (!d.qty) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                            } else {
                                // frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                            }
                        }

                        if (!d.concentration) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                                //frappe.throw(d.doctype + " Row: "+ d.idx +" Please add received or accepted concentration")
                            } else {
                                // frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add concentration")
                            }
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")) {
                            frappe.model.set_value(d.doctype, d.name, 'quantity', d.accepted_quantity || d.receive_quantity);
                        } else {
                            if (d.quantity != flt(d.qty) * flt(d.concentration) / 100) {
                                frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty) * flt(d.concentration) / 100);
                            }
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_quantity")) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                        } else {
                            if (d.rate != flt(d.quantity) * flt(d.price) / flt(d.qty)) {
                                frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity) * flt(d.price) / flt(d.qty));
                            }
                        }
                    } else {
                        if (frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity', flt(d.receive_qty));
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "supplier_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity', flt(d.supplier_qty));
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'accepted_quantity', flt(d.accepted_qty));
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_qty") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.accepted_qty) || flt(d.receive_qty));
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_concentration") && frappe.meta.get_docfield("Purchase Invoice Item", "received_concentration")) {
                            frappe.model.set_value(d.doctype, d.name, 'concentration', flt(d.accepted_concentration) || flt(d.received_concentration));
                        }

                        if (!frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty") && (!d.packing_size || !d.no_of_packages)) {
                            if (d.quantity && d.qty != flt(d.quantity)) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity))
                            }
                        }
                        if (!d.qty) {
                            if (frappe.meta.get_docfield("Purchase Invoice Item", "receive_qty")) {
                                // frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                            } else {
                                //  frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                            }
                        }

                        if (frappe.meta.get_docfield("Purchase Invoice Item", "accepted_quantity") && frappe.meta.get_docfield("Purchase Invoice Item", "receive_quantity")) {
                            frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.accepted_quantity) || flt(d.receive_quantity));
                        } else {
                            if (d.qty != d.quantity) {
                                frappe.model.set_value(d.doctype, d.name, 'quantity', flt(d.qty));
                            }
                            if (d.rate != d.price) {
                                frappe.model.set_value(d.doctype, d.name, 'rate', d.price);
                            }
                        }

                    }
                    if (frappe.meta.get_docfield("Purchase Invoice Item", "short_quantity")) {
                        frappe.model.set_value(d.doctype, d.name, 'short_quantity', flt(d.quantity) - flt(d.supplier_quantity));
                        if (d.short_quantity) {
                            frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                        }
                    }

                    if (frappe.meta.get_docfield("Purchase Invoice Item", "amount_difference")) {
                        frappe.model.set_value(d.doctype, d.name, 'amount_difference', flt(d.price) * flt(d.short_quantity));
                    }

                });
            } else {
                frm.doc.items.forEach(function(d) {
                    if(!d.ignore_calculation) {
                        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                            if(r.maintain_as_is_stock){
                                frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                            } else {
                                if (d.packing_size && d.no_of_packages) {
                                    if (d.qty != d.packing_size * d.no_of_packages) {
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                    }
                                    if (d.received_qty != d.packing_size * d.no_of_packages) {
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                            }
                        });
                    } else {
                        if(d.ignore_calculation){
                            if (d.packing_size && d.no_of_packages) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                            }
                        }
                    }
				}); 
            }
        });
    },
});
frappe.ui.form.on("Purchase Invoice Item", {
    receive_no_of_packages: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    packing_size: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    tare_weight: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_packing_size: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_no_of_packages: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_no_of_packages: function(frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
});