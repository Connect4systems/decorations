from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from decorations.decorations.doctype.clearnce.clearnce import Clearnce


class TestClearnce(FrappeTestCase):
	def make_clearnce(self):
		return frappe.get_doc(
			{
				"doctype": "Clearnce",
				"name": "CLR-TEST",
				"project": "Project Test",
				"date": "2026-10-03",
				"customer": "Customer Test",
				"company": "Company Test",
				"currency": "EGP",
				"supervision_percent": 10,
				"costs": [
					{"cost": "COST-1", "cost_type": "Paint", "amount": 100, "note": "Paint"},
					{"cost": "COST-2", "cost_type": "Labor", "amount": 50},
				],
			}
		)

	def test_supervision_and_total(self):
		doc = self.make_clearnce()
		doc.calculate_totals()
		self.assertEqual(doc.total_cost, 150)
		self.assertEqual(doc.supervision, 15)
		self.assertEqual(doc.total_amount, 165)

	def test_duplicate_cost_rejected(self):
		doc = self.make_clearnce()
		doc.costs[1].cost = "COST-1"
		cost = MagicMock(
			project=doc.project, docstatus=1, status="Pending", sales_invoice=None, clearnce=None
		)
		with (
			patch.object(Clearnce, "set_project_details"),
			patch("frappe.get_doc", return_value=cost),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_already_invoiced_cost_rejected(self):
		doc = self.make_clearnce()
		cost = MagicMock(project=doc.project, docstatus=1, status="Unpaid", sales_invoice="SI-OTHER")
		with (
			patch.object(Clearnce, "set_project_details"),
			patch("frappe.get_doc", return_value=cost),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_submit_locks_then_revalidates(self):
		doc = self.make_clearnce()
		with patch("frappe.db.get_value") as lock, patch.object(Clearnce, "validate") as validate:
			doc.before_submit()
		self.assertEqual([call.args[1] for call in lock.call_args_list], ["COST-1", "COST-2"])
		self.assertTrue(all(call.kwargs["for_update"] for call in lock.call_args_list))
		validate.assert_called_once_with(lock=True)

	def test_submit_creates_cost_and_supervision_invoice_lines(self):
		doc = self.make_clearnce()
		doc.calculate_totals()
		invoice = MagicMock()
		invoice.name = "SI-TEST"
		with (
			patch("frappe.new_doc", return_value=invoice),
			patch("frappe.db.get_value", side_effect=["PAINT-ITEM", "LABOR-ITEM"]),
			patch("frappe.db.get_single_value", return_value="SUPERVISION-ITEM"),
			patch("frappe.db.set_value") as cost_links,
			patch.object(Clearnce, "db_set") as invoice_link,
			patch("decorations.billing.sync_invoice") as sync,
			patch("frappe.msgprint"),
		):
			doc.on_submit()
		lines = [call.args[1] for call in invoice.append.call_args_list]
		self.assertEqual(
			[row["item_code"] for row in lines], ["PAINT-ITEM", "LABOR-ITEM", "SUPERVISION-ITEM"]
		)
		self.assertEqual([row["rate"] for row in lines], [100, 50, 15])
		self.assertEqual(invoice.custom_clearnce, "CLR-TEST")
		self.assertEqual(invoice.project, doc.project)
		invoice.insert.assert_called_once_with()
		invoice.submit.assert_called_once_with()
		invoice_link.assert_called_once_with("sales_invoice", "SI-TEST")
		self.assertEqual(cost_links.call_count, 2)
		sync.assert_called_once_with("SI-TEST")

	def test_fetch_replaces_rows_and_filters_pending_costs(self):
		doc = self.make_clearnce()
		cost = frappe._dict(name="COST-3", cost_type="Paint", note="New paint", amount=200, attachment=None)
		with (
			patch.object(Clearnce, "check_permission"),
			patch.object(Clearnce, "set_project_details"),
			patch("frappe.get_doc"),
			patch("frappe.get_list", return_value=[cost]) as query,
		):
			doc.fetch_cost()
		self.assertEqual(len(doc.costs), 1)
		self.assertEqual(doc.costs[0].cost, "COST-3")
		self.assertEqual(doc.total_amount, 220)
		filters = query.call_args.kwargs["filters"]
		self.assertEqual(filters["project"], doc.project)
		self.assertEqual(filters["status"], "Pending")
		self.assertEqual(filters["docstatus"], 1)

	def test_cancel_releases_only_costs_still_linked_to_this_clearnce(self):
		doc = self.make_clearnce()
		doc.sales_invoice = "SI-TEST"
		invoice = MagicMock(docstatus=1)
		with (
			patch("frappe.get_doc", return_value=invoice),
			patch("frappe.get_all", return_value=["COST-1"]) as costs,
			patch("frappe.db.set_value") as release,
		):
			doc.on_cancel()
		invoice.cancel.assert_called_once_with()
		costs.assert_called_once_with("Cost", filters={"clearnce": doc.name}, pluck="name")
		release.assert_called_once_with(
			"Cost", "COST-1", {"clearnce": None, "sales_invoice": None, "status": "Pending"}
		)
