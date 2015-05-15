// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Consolidated Accounts Receivable"] = {
	"filters": [
		{
			"fieldname":"consolidation",
			"label": __("Consolidation"),
			"fieldtype": "Select",
			"options": "yes",
			"default": "yes"
		},
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"get_query": function() {
				var consolidation = frappe.query_report.filters_by_name.consolidation.get_value();
				return {
					"query": "erpnext.controllers.queries.get_account_list", 
					"filters": {
						"report_type": "Balance Sheet",
						"consolidation": consolidation,
						"master_type": "Customer"
					}
				}
			}
		},
		{
			"fieldname":"report_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": get_today()
		},
		{
			"fieldname":"ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			"options": 'Posting Date' + NEWLINE + 'Due Date',
			"default": "Posting Date"
		}
	]
}