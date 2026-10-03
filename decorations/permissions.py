"""Install the decoration workflow role without replacing other roles' permissions."""

import frappe
from frappe.permissions import rights, setup_custom_perms

MANAGER_ROLE = "Manager"
MANAGED_DOCTYPES = (
	"Cost", "Cost Type", "Clearnce", "Decoration Settings",
	"Project", "Item", "Customer", "Sales Invoice", "Journal Entry", "Payment Entry", "File",
)
READ_ONLY_DOCTYPES = (
	"Account", "GL Entry", "Mode of Payment", "Company", "Cost Center", "Currency",
	"Item Group", "UOM", "Project Type", "Territory", "Customer Group",
	"Price List", "Item Price", "Sales Taxes and Charges Template", "Tax Category",
	"Payment Terms Template", "Payment Term", "Fiscal Year", "Warehouse",
)
READ_RIGHTS = {"select", "read", "report", "export", "print", "email"}


def setup_manager_role():
	if not frappe.db.exists("Role", MANAGER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": MANAGER_ROLE, "desk_access": 1}).insert(
			ignore_permissions=True
		)

	for doctype in MANAGED_DOCTYPES + READ_ONLY_DOCTYPES:
		meta = frappe.get_meta(doctype)
		allowed = set(rights) if doctype in MANAGED_DOCTYPES else READ_RIGHTS.copy()
		if not meta.is_submittable:
			allowed.difference_update({"submit", "cancel", "amend"})
		if not meta.allow_import:
			allowed.discard("import")
		if meta.issingle:
			allowed.difference_update({"create", "delete", "report", "import", "export"})

		# Frappe custom permissions override standard permissions, so copy existing
		# rules before adding ours. Existing custom rules remain intact.
		setup_custom_perms(doctype)
		filters = {"parent": doctype, "role": MANAGER_ROLE, "permlevel": 0, "if_owner": 0}
		name = frappe.db.get_value("Custom DocPerm", filters, "name")
		permission = frappe.get_doc("Custom DocPerm", name) if name else frappe.get_doc({
			"doctype": "Custom DocPerm", "parenttype": "DocType", "parentfield": "permissions",
			**filters,
		})
		permission.update({right: int(right in allowed) for right in rights})
		permission.save(ignore_permissions=True)
		frappe.clear_cache(doctype=doctype)

	setup_general_ledger_access()
	frappe.clear_cache()


def setup_general_ledger_access():
	# Custom Role is the supported way to extend a standard report's access.
	# Seed from the existing report roles so their access is preserved.
	name = frappe.db.get_value("Custom Role", {"report": "General Ledger"}, "name")
	if name:
		custom_role = frappe.get_doc("Custom Role", name)
	else:
		report = frappe.get_doc("Report", "General Ledger")
		custom_role = frappe.get_doc({
			"doctype": "Custom Role", "report": report.name,
			"roles": [{"role": row.role} for row in report.roles],
		})
	if MANAGER_ROLE not in {row.role for row in custom_role.roles}:
		custom_role.append("roles", {"role": MANAGER_ROLE})
		custom_role.save(ignore_permissions=True)
