import frappe
from frappe.tests.utils import FrappeTestCase

from decorations.permissions import MANAGER_ROLE, setup_manager_role


class TestManagerPermissions(FrappeTestCase):
	def test_setup_is_repeatable_and_preserves_other_roles(self):
		original_permissions = [
			row.as_dict() for row in frappe.get_meta("Sales Invoice").permissions
			if row.role != MANAGER_ROLE
		]
		setup_manager_role()
		for original in original_permissions:
			matching = [
				row for row in frappe.get_meta("Sales Invoice").permissions
				if row.role == original["role"] and row.permlevel == original["permlevel"]
				and row.if_owner == original.get("if_owner", 0)
			]
			self.assertTrue(matching)
			for right in ("read", "write", "create", "submit", "cancel", "delete"):
				self.assertEqual(matching[0].get(right), original.get(right))
		before = frappe.get_all(
			"Custom DocPerm", filters={"parent": "Sales Invoice"},
			fields=["name", "role", "read", "write", "create", "submit", "cancel", "delete"],
			order_by="name",
		)
		ledger = frappe.get_doc(
			"Custom Role", frappe.db.get_value("Custom Role", {"report": "General Ledger"}, "name")
		)
		roles = [row.role for row in ledger.roles]
		setup_manager_role()
		self.assertEqual(before, frappe.get_all(
			"Custom DocPerm", filters={"parent": "Sales Invoice"},
			fields=["name", "role", "read", "write", "create", "submit", "cancel", "delete"],
			order_by="name",
		))
		ledger.reload()
		self.assertEqual(roles, [row.role for row in ledger.roles])
		self.assertEqual(roles.count(MANAGER_ROLE), 1)

	def test_manager_can_complete_workflow_with_read_only_accounting_masters(self):
		setup_manager_role()
		for doctype in ("Cost", "Clearnce", "Sales Invoice", "Journal Entry", "Payment Entry"):
			with self.subTest(doctype=doctype):
				permission = self.manager_permission(doctype)
				for right in ("read", "create", "write", "submit", "cancel", "delete", "amend"):
					self.assertEqual(permission.get(right), 1, f"{doctype}: {right}")
		for doctype in ("Cost Type", "Item", "Project", "Customer"):
			permission = self.manager_permission(doctype)
			for right in ("read", "create", "write", "delete"):
				self.assertEqual(permission.get(right), 1, f"{doctype}: {right}")
		for doctype in ("Account", "GL Entry", "Mode of Payment"):
			permission = self.manager_permission(doctype)
			self.assertEqual(permission.read, 1)
			self.assertEqual(permission.report, 1)
			for right in ("create", "write", "submit", "cancel", "delete", "amend"):
				self.assertFalse(permission.get(right), f"{doctype}: {right}")
		self.assertEqual(self.manager_permission("Decoration Settings").write, 1)
		self.assertEqual(self.manager_permission("File").create, 1)

	def manager_permission(self, doctype):
		permissions = [
			row for row in frappe.get_meta(doctype).permissions
			if row.role == MANAGER_ROLE and row.permlevel == 0 and not row.if_owner
		]
		self.assertEqual(len(permissions), 1)
		return permissions[0]
