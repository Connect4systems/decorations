app_name = "decorations"
app_title = "Decorations"
app_publisher = "Connect 4 Systems"
app_description = "App for small decoration company"
app_email = "connect4systems@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

after_migrate = "decorations.setup.after_migrate"
after_install = "decorations.setup.after_migrate"

doc_events = {
	"Sales Invoice": {
		"on_submit": "decorations.billing.invoice_updated",
		"on_update_after_submit": "decorations.billing.invoice_updated",
		"on_cancel": "decorations.billing.invoice_updated",
	},
	"Payment Entry": {
		"on_submit": "decorations.billing.payment_updated",
		"on_cancel": "decorations.billing.payment_updated",
	},
	"Journal Entry": {
		"on_submit": "decorations.billing.payment_updated",
		"on_cancel": "decorations.billing.payment_updated",
	},
}

scheduler_events = {"hourly": ["decorations.billing.sync_cost_statuses"]}

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "decorations",
# 		"logo": "/assets/decorations/logo.png",
# 		"title": "Decorations",
# 		"route": "/decorations",
# 		"has_permission": "decorations.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/decorations/css/decorations.css"
# app_include_js = "/assets/decorations/js/decorations.js"

# include js, css files in header of web template
# web_include_css = "/assets/decorations/css/decorations.css"
# web_include_js = "/assets/decorations/js/decorations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "decorations/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "decorations/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "decorations.utils.jinja_methods",
# 	"filters": "decorations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "decorations.install.before_install"
# after_install = "decorations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "decorations.uninstall.before_uninstall"
# after_uninstall = "decorations.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "decorations.utils.before_app_install"
# after_app_install = "decorations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "decorations.utils.before_app_uninstall"
# after_app_uninstall = "decorations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "decorations.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["decorations.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"decorations.tasks.all"
# 	],
# 	"daily": [
# 		"decorations.tasks.daily"
# 	],
# 	"hourly": [
# 		"decorations.tasks.hourly"
# 	],
# 	"weekly": [
# 		"decorations.tasks.weekly"
# 	],
# 	"monthly": [
# 		"decorations.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "decorations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "decorations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "decorations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["decorations.utils.before_request"]
# after_request = ["decorations.utils.after_request"]

# Job Events
# ----------
# before_job = ["decorations.utils.before_job"]
# after_job = ["decorations.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"decorations.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
