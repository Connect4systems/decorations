import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form


class Clearnce(Document):
	@frappe.whitelist()
	def fetch_cost(self):
		self.check_permission("write")
		if self.docstatus != 0:
			frappe.throw(_("Costs can only be fetched into a draft Clearnce."))
		if not self.project:
			frappe.throw(_("Please select a Project first."))
		frappe.get_doc("Project", self.project).check_permission("read")
		costs = frappe.get_list(
			"Cost",
			filters={
				"project": self.project,
				"docstatus": 1,
				"status": "Pending",
				"sales_invoice": ["is", "not set"],
				"clearnce": ["is", "not set"],
			},
			fields=["name", "cost_type", "note", "amount", "attachment"],
			order_by="date asc, name asc",
			limit_page_length=0,
		)
		self.set("costs", [])
		for cost in costs:
			self.append(
				"costs",
				{
					"cost": cost.name,
					"cost_type": cost.cost_type,
					"note": cost.note,
					"amount": cost.amount,
					"attachment": cost.attachment,
				},
			)
		self.set_project_details()
		self.calculate_totals()
		return self.as_dict()

	def set_project_details(self):
		project = frappe.get_doc("Project", self.project)
		project.check_permission("read")
		self.customer = project.customer
		self.company = project.company
		self.supervision_percent = flt(project.custom_supervision)
		if not self.customer or not self.company:
			frappe.throw(_("Please set Customer and Company on the Project."))
		if self.supervision_percent < 0:
			frappe.throw(_("Project Supervision percentage cannot be negative."))
		self.currency = frappe.get_cached_value("Company", self.company, "default_currency")

	def validate(self, lock=False):
		self.set_project_details()
		if not self.costs:
			frappe.throw(_("Please fetch pending Costs for this Project."))
		seen = set()
		for row in self.costs:
			if row.cost in seen:
				frappe.throw(_("Cost {0} appears more than once.").format(row.cost))
			seen.add(row.cost)
			cost = frappe.get_doc("Cost", row.cost, for_update=lock)
			cost.check_permission("read")
			if (
				cost.project != self.project
				or cost.docstatus != 1
				or cost.status != "Pending"
				or cost.sales_invoice
				or cost.clearnce
			):
				frappe.throw(
					_("Cost {0} is no longer pending for this Project. Fetch Costs again.").format(row.cost)
				)
			for field in ("cost_type", "note", "amount", "attachment"):
				row.set(field, cost.get(field))
		self.calculate_totals()

	def calculate_totals(self):
		self.total_cost = flt(sum(flt(row.amount) for row in self.costs), self.precision("total_cost"))
		self.supervision = flt(
			self.total_cost * flt(self.supervision_percent) / 100, self.precision("supervision")
		)
		self.total_amount = flt(self.total_cost + self.supervision, self.precision("total_amount"))

	def before_submit(self):
		# Serialize competing clearances, then recheck eligibility under the locks.
		for name in sorted(row.cost for row in self.costs):
			frappe.db.get_value("Cost", name, "name", for_update=True)
		self.validate(lock=True)

	def on_submit(self):
		if self.sales_invoice:
			frappe.throw(_("This Clearnce already has a Sales Invoice."))
		invoice = frappe.new_doc("Sales Invoice")
		invoice.company = self.company
		invoice.customer = self.customer
		invoice.project = self.project
		invoice.currency = self.currency
		invoice.conversion_rate = 1
		invoice.posting_date = self.date
		invoice.set_posting_time = 1
		invoice.custom_clearnce = self.name
		invoice.remarks = _("Clearnce: {0}").format(self.name)
		for row in self.costs:
			item = frappe.db.get_value("Cost Type", row.cost_type, "sales_item")
			if not item:
				frappe.throw(_("Please set Sales Item on Cost Type {0}.").format(row.cost_type))
			invoice.append(
				"items",
				{
					"item_code": item,
					"qty": 1,
					"rate": row.amount,
					"description": row.note or row.cost_type,
					"project": self.project,
				},
			)
		if self.supervision:
			item = frappe.db.get_single_value("Decoration Settings", "supervision")
			if not item:
				frappe.throw(_("Please set the Supervision item in Decoration Settings."))
			invoice.append(
				"items",
				{
					"item_code": item,
					"qty": 1,
					"rate": self.supervision,
					"description": _("Project supervision ({0}%)").format(self.supervision_percent),
					"project": self.project,
				},
			)
		invoice.set_missing_values()
		invoice.insert()
		invoice.submit()
		self.db_set("sales_invoice", invoice.name)
		for row in self.costs:
			frappe.db.set_value("Cost", row.cost, {"clearnce": self.name, "sales_invoice": invoice.name})
		from decorations.billing import sync_invoice

		sync_invoice(invoice.name)
		frappe.msgprint(
			_("Created submitted Sales Invoice {0}.").format(get_link_to_form("Sales Invoice", invoice.name)),
			alert=True,
			indicator="green",
		)

	def on_cancel(self):
		if self.sales_invoice:
			invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)
			if invoice.docstatus == 1:
				invoice.cancel()
		for name in frappe.get_all("Cost", filters={"clearnce": self.name}, pluck="name"):
			frappe.db.set_value("Cost", name, {"clearnce": None, "sales_invoice": None, "status": "Pending"})
