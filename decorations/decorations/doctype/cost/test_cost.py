# Copyright (c) 2026, Connect 4 Systems and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from decorations.decorations.doctype.cost.cost import Cost


class TestCost(FrappeTestCase):
	def make_cost(self):
		return frappe.get_doc({
			"doctype": "Cost", "name": "COST-TEST", "date": "2026-10-03",
			"project": "Project Test", "cost_type": "Materials", "amount": 125,
			"mode_of_payment": "Cash", "note": "Paint for project",
		})

	def test_submit_posts_balanced_project_entry(self):
		cost = self.make_cost()
		journal = MagicMock(name="journal")
		journal.name = "JE-TEST"

		def cached_value(doctype, name, field, **kwargs):
			if doctype == "Company":
				return "EGP" if field == "default_currency" else "Main - TC"
			return frappe._dict(company="Test Company", is_group=0, disabled=0, account_currency="EGP")

		with (
			patch("frappe.db.get_value", side_effect=["Test Company", "Materials - TC", "Cash - TC"]),
			patch("frappe.get_cached_value", side_effect=cached_value),
			patch("frappe.get_doc", return_value=journal) as get_doc,
			patch.object(Cost, "copy_attachments") as attachments,
			patch.object(Cost, "db_set") as db_set,
			patch("frappe.msgprint") as message,
		):
			cost.on_submit()
		entry = get_doc.call_args.args[0]
		self.assertEqual(entry["company"], "Test Company")
		self.assertEqual(entry["posting_date"], cost.date)
		self.assertIn(cost.note, entry["user_remark"])
		self.assertIn(cost.name, entry["user_remark"])
		self.assertEqual(entry["accounts"][0]["debit_in_account_currency"], 125)
		self.assertEqual(entry["accounts"][1]["credit_in_account_currency"], 125)
		self.assertEqual(entry["accounts"][0]["account"], "Materials - TC")
		self.assertEqual(entry["accounts"][1]["account"], "Cash - TC")
		self.assertTrue(all(row["project"] == cost.project for row in entry["accounts"]))
		journal.insert.assert_called_once_with()
		journal.submit.assert_called_once_with()
		attachments.assert_called_once_with("JE-TEST")
		db_set.assert_called_once_with("journal_entry", "JE-TEST")
		self.assertIn("JE-TEST", message.call_args.args[0])

	def test_missing_payment_account_blocks_posting(self):
		cost = self.make_cost()
		with (
			patch("frappe.db.get_value", side_effect=["Test Company", "Materials - TC", None]),
			patch("frappe.get_doc") as get_doc,
			self.assertRaises(frappe.ValidationError),
		):
			cost.on_submit()
		get_doc.assert_not_called()

	def test_cancel_cancels_submitted_journal(self):
		cost = self.make_cost()
		cost.journal_entry = "JE-TEST"
		journal = MagicMock(docstatus=1)
		with patch("frappe.get_doc", return_value=journal):
			cost.on_cancel()
		journal.cancel.assert_called_once_with()

	def test_copies_private_attachment(self):
		cost = self.make_cost()
		file = frappe._dict(file_name="receipt.pdf", file_url="/private/files/receipt.pdf", is_private=1)
		cost.attachment = file.file_url
		with (
			patch("frappe.get_all", return_value=[file]),
			patch("frappe.get_doc") as get_doc,
		):
			cost.copy_attachments("JE-TEST")
		self.assertEqual(get_doc.call_count, 1)
		attachment = get_doc.call_args.args[0]
		self.assertEqual(attachment["attached_to_name"], "JE-TEST")
		self.assertEqual(attachment["is_private"], 1)
		self.assertEqual(attachment["file_url"], file.file_url)
