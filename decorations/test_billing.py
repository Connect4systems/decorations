from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from decorations.billing import cost_status, invoice_updated, payment_updated, sync_invoice


class TestBilling(FrappeTestCase):
	def test_balance_and_due_date_follow_erpnext_status_rules(self):
		for outstanding, due_date, expected in (
			(100, add_days(nowdate(), 10), "Unpaid"),
			(40, add_days(nowdate(), 10), "Partly Paid"),
			(40, add_days(nowdate(), -1), "Overdue"),
			(0, add_days(nowdate(), -1), "Paid"),
		):
			with self.subTest(expected=expected):
				invoice = frappe.get_doc(
					{
						"doctype": "Sales Invoice",
						"name": "SI-STATUS-TEST",
						"docstatus": 1,
						"currency": "EGP",
						"party_account_currency": "EGP",
						"grand_total": 100,
						"rounded_total": 100,
						"disable_rounded_total": 0,
						"outstanding_amount": outstanding,
						"due_date": due_date,
					}
				)
				with (
					patch.object(type(invoice), "is_internal_transfer", return_value=False),
					patch("frappe.db.get_value", return_value=None),
				):
					self.assertEqual(cost_status(invoice), expected)

	def test_native_invoice_status_is_used(self):
		for status in ("Unpaid", "Partly Paid", "Paid", "Overdue", "Partly Paid and Discounted"):
			with self.subTest(status=status):
				invoice = MagicMock(docstatus=1, status=status)
				self.assertEqual(cost_status(invoice), status.removesuffix(" and Discounted"))
				invoice.set_status.assert_called_once_with()

	def test_cancelled_invoice_releases_costs(self):
		invoice = MagicMock(docstatus=2)
		with (
			patch("frappe.get_doc", return_value=invoice),
			patch("frappe.get_all", return_value=["COST-1"]),
			patch("frappe.db.set_value") as update,
		):
			sync_invoice("SI-TEST")
		update.assert_called_once_with(
			"Cost", "COST-1", {"status": "Pending", "sales_invoice": None, "clearnce": None}
		)

	def test_payment_references_are_deduplicated(self):
		doc = frappe._dict(
			references=[
				frappe._dict(reference_doctype="Sales Invoice", reference_name="SI-TEST"),
				frappe._dict(reference_doctype="Sales Invoice", reference_name="SI-TEST"),
				frappe._dict(reference_doctype="Purchase Invoice", reference_name="PI-TEST"),
			]
		)
		with (
			patch("frappe.db.get_value", return_value="CLR-TEST"),
			patch("decorations.billing.sync_invoice") as sync,
		):
			payment_updated(doc)
		sync.assert_called_once_with("SI-TEST")

	def test_cancel_hook_preserves_standard_ignored_links(self):
		doc = frappe._dict(
			name="SI-TEST", custom_clearnce="CLR-TEST", docstatus=2, ignore_linked_doctypes=("GL Entry",)
		)
		with patch("decorations.billing.sync_invoice"):
			invoice_updated(doc)
		self.assertEqual(doc.ignore_linked_doctypes, ("GL Entry", "Cost", "Clearnce"))
