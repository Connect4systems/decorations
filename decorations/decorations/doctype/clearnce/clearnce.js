frappe.ui.form.on("Clearnce", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Fetch Cost"), () => {
				frm.call("fetch_cost").then((r) => {
					if (r.message) {
						frappe.model.sync(r.message);
						frm.refresh_fields();
						frm.dirty();
						if (!frm.doc.costs.length) {
							frappe.msgprint(__("No pending Costs found for this Project."));
						}
					}
				});
			});
		}
	},
	project(frm) {
		frm.clear_table("costs");
		frm.set_value({ total_cost: 0, supervision: 0, total_amount: 0 });
		frm.refresh_field("costs");
	},
});
