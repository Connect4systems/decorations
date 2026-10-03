import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_migrate():
	create_custom_fields(
		{
			"Sales Invoice": [
				{
					"fieldname": "custom_clearnce",
					"label": "Clearnce",
					"fieldtype": "Link",
					"options": "Clearnce",
					"insert_after": "project",
					"read_only": 1,
					"no_copy": 1,
				}
			],
		}
	)
	# Existing submitted Costs become available to the first clearance.
	for name in frappe.get_all(
		"Cost",
		filters={"docstatus": 1, "status": ["is", "not set"], "sales_invoice": ["is", "not set"]},
		pluck="name",
	):
		frappe.db.set_value("Cost", name, "status", "Pending", update_modified=False)
