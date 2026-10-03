"""Keep project cost billing status in step with invoice balances."""

import frappe
from frappe.utils import flt


def cost_status(invoice):
	if invoice.docstatus != 1:
		return "Pending"
	# ERPNext handles payment schedules, currency, due dates, and rounding.
	invoice.set_status()
	status = invoice.status.removesuffix(" and Discounted")
	if status in ("Unpaid", "Partly Paid", "Paid", "Overdue"):
		return status
	return "Paid" if flt(invoice.outstanding_amount) <= 0 else "Unpaid"


def sync_invoice(name):
	invoice = frappe.get_doc("Sales Invoice", name)
	status = cost_status(invoice)
	for cost in frappe.get_all("Cost", filters={"sales_invoice": name, "docstatus": 1}, pluck="name"):
		values = {"status": status}
		if invoice.docstatus == 2:
			values.update(sales_invoice=None, clearnce=None)
		frappe.db.set_value("Cost", cost, values)


def invoice_updated(doc, method=None):
	if doc.get("custom_clearnce"):
		if doc.docstatus == 2:
			# The invoice controller replaces this list in its own on_cancel method.
			doc.ignore_linked_doctypes = (*(doc.get("ignore_linked_doctypes") or ()), "Cost", "Clearnce")
		sync_invoice(doc.name)


def payment_updated(doc, method=None):
	names = set()
	for row in doc.get("references") or []:
		if row.reference_doctype == "Sales Invoice":
			names.add(row.reference_name)
	for row in doc.get("accounts") or []:
		if row.reference_type == "Sales Invoice":
			names.add(row.reference_name)
	for name in names:
		if name and frappe.db.get_value("Sales Invoice", name, "custom_clearnce"):
			sync_invoice(name)


def sync_cost_statuses():
	# Also covers time passing, reconciliation, and balance changes made without document events.
	names = set(
		frappe.get_all(
			"Cost", filters={"docstatus": 1, "sales_invoice": ["is", "set"]}, pluck="sales_invoice"
		)
	)
	for name in names:
		sync_invoice(name)
