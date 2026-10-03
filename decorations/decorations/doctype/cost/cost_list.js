frappe.listview_settings["Cost"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {
			Pending: "orange",
			Unpaid: "red",
			"Partly Paid": "orange",
			Paid: "green",
			Overdue: "red",
		};
		if (doc.docstatus === 1 && doc.status) {
			return [__(doc.status), colors[doc.status], `status,=,${doc.status}`];
		}
	},
};
