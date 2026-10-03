# Copyright (c) 2026, Connect 4 Systems and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form


class Cost(Document):
	def validate(self):
		if flt(self.amount, self.precision("amount")) <= 0:
			frappe.throw(_("Amount must be greater than zero."))

	def on_submit(self):
		if self.journal_entry:
			frappe.throw(_("This Cost already has a Journal Entry."))

		company = frappe.db.get_value("Project", self.project, "company")
		if not company:
			frappe.throw(_("Please set a Company on the Project."))
		debit_account = frappe.db.get_value("Cost Type", self.cost_type, "account")
		if not debit_account:
			frappe.throw(_("Please set an Account on the Cost Type."))
		credit_account = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": self.mode_of_payment, "parenttype": "Mode of Payment", "company": company},
			"default_account",
		)
		if not credit_account:
			frappe.throw(_("Please set a payment account for {0} in Mode of Payment {1}.").format(
				company, self.mode_of_payment
			))
		if debit_account == credit_account:
			frappe.throw(_("Cost and payment accounts must be different."))

		currency = frappe.get_cached_value("Company", company, "default_currency")
		for account_name in (debit_account, credit_account):
			account = frappe.get_cached_value(
				"Account", account_name, ["company", "is_group", "disabled", "account_currency"], as_dict=True
			)
			if account.company != company or account.is_group or account.disabled:
				frappe.throw(_("Account {0} must be an enabled ledger account in {1}.").format(account_name, company))
			if account.account_currency and account.account_currency != currency:
				frappe.throw(_("Account {0} must use the company currency {1}.").format(account_name, currency))

		amount = flt(self.amount, self.precision("amount"))
		cost_center = frappe.get_cached_value("Company", company, "cost_center")
		journal_entry = frappe.get_doc({
			"doctype": "Journal Entry",
			"voucher_type": "Journal Entry",
			"company": company,
			"posting_date": self.date,
			"mode_of_payment": self.mode_of_payment,
			"user_remark": "\n".join(filter(None, [_("Cost: {0}").format(self.name), self.note])),
			"accounts": [
				{"account": debit_account, "debit_in_account_currency": amount,
				 "project": self.project, "cost_center": cost_center},
				{"account": credit_account, "credit_in_account_currency": amount,
				 "project": self.project, "cost_center": cost_center},
			],
		})
		journal_entry.insert()
		self.copy_attachments(journal_entry.name)
		journal_entry.submit()
		self.db_set("journal_entry", journal_entry.name)
		frappe.msgprint(
			_("Cost created submitted Journal Entry {0}.").format(
				get_link_to_form("Journal Entry", journal_entry.name)
			), alert=True, indicator="green",
		)

	def copy_attachments(self, journal_entry):
		files = frappe.get_all(
			"File", filters={"attached_to_doctype": "Cost", "attached_to_name": self.name},
			fields=["file_name", "file_url", "is_private"],
		)
		if self.attachment and not any(file.file_url == self.attachment for file in files):
			file = frappe.db.get_value(
				"File", {"file_url": self.attachment}, ["file_name", "file_url", "is_private"], as_dict=True
			)
			if not file:
				frappe.throw(_("Please upload the Cost attachment before submitting."))
			files.append(file)
		for file in files:
			frappe.get_doc({
				"doctype": "File", "file_name": file.file_name, "file_url": file.file_url,
				"is_private": file.is_private, "attached_to_doctype": "Journal Entry",
				"attached_to_name": journal_entry,
			}).insert()

	def on_cancel(self):
		if self.journal_entry:
			journal_entry = frappe.get_doc("Journal Entry", self.journal_entry)
			if journal_entry.docstatus == 1:
				journal_entry.cancel()
