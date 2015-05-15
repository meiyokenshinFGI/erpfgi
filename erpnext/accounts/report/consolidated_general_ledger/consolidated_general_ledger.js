// Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Consolidated General Ledger"] = {
	"filters": [
		{
			"fieldname":"consolidation",
			"label": __("Consolidation"),
			"fieldtype": "Select",
			"options": "yes",
			"default": "yes",
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldtype": "Break",
		},
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"get_query": function() {
				var consolidation = frappe.query_report.filters_by_name.consolidation.get_value();
				return {
					"doctype": "Account", 
					"filters": {
						"consolidation": consolidation,
					}
				}
			}
		},
		{
			"fieldname":"voucher_no",
			"label": __("Voucher No"),
			"fieldtype": "Data",
		},
		{
			"fieldname":"group_by_voucher",
			"label": __("Group by Voucher"),
			"fieldtype": "Check",
			"default": 1
		},
		{
			"fieldname":"group_by_account",
			"label": __("Group by Account"),
			"fieldtype": "Check",
		}
	]
}