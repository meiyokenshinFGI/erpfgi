# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, _dict
from frappe.utils import (flt, getdate, get_first_day, get_last_day,
	add_months, add_days, formatdate,nowdate)
from erpnext.accounts.utils import (get_balance_on)

def get_cash_and_bank_account():
	account_list=frappe.db.sql("""select name from tabAccount where account_type IN ("Bank" ,"Cash") """,as_list=1)
	if account_list :
		return account_list
	else:
		return None

#def get_last_cash(selected):
#	account_data=frappe.db.sql("""select  """)

def execute(filters=None):
	
	period_list = get_period_list(filters.get("fiscal_year"), filters.periodicity)
	account_list=get_cash_and_bank_account()
	if account_list==None:
		frappe.throw("Error, There is no Cash or bank Account to be tracked down")
	selected=""
	beginning_balance=0
	sd=period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	for ba in account_list:
		if selected=="":
			selected=ba[0]
		else:
			selected="""{}","{}""".format(selected,ba[0])
		beginning_balance+=get_balance_on(ba[0],sd)
	selected = """ "{}" """.format(selected)
	asset = get_data(filters.company, "Asset", "Credit", period_list, selected, ignore_closing_entries=True)
	liability = get_data(filters.company, "Liability", "Credit", period_list, selected, ignore_closing_entries=True)
	
	income = get_data(filters.company, "Income", "Credit", period_list, selected, ignore_closing_entries=True)
	expense = get_data(filters.company, "Expense", "Debit", period_list,  selected, ignore_closing_entries=True)
	net_profit_loss = get_net_profit_loss(income, expense, period_list)
	
	data = []
	#data.extend(income or [])
	#data.extend(expense or [])
	
	if net_profit_loss:
		data.append(net_profit_loss)
	data.extend(asset or [])
	data.extend(liability or [])
	#data.extend(liability or [])
	data=get_total_change (beginning_balance,net_profit_loss,asset,liability,period_list,data)
	columns = get_columns(period_list)
	return columns, data

def get_total_change (beginning_balance,net_profit_loss,asset,liability,period_list,data):
	sa = {
		"account_name": _("Beginning Balance"),
		"account": None,
		"warn_if_negative": True
	}
	movement={
		"account_name": _("The increase and decrease in cash"),
		"account": None,
		"warn_if_negative": True
	}
	total={
		"account_name": _("Total"),
		"account": None,
		"warn_if_negative": True
	}
	#today=getdate(nowdate())
	for period in period_list:
		pl=0
		a=0
		l=0
		if net_profit_loss:
			pl=net_profit_loss[period.key]
		if asset:
			a=asset[-2][period.key]
		if liability:
			l=liability[-2][period.key]
		#if today < period.from_date:
		#	sa[period.key] = beginning_balance
		#	movement[period.key]=0
		#	total[period.key]=beginning_balance
		#else:
		sa[period.key] = beginning_balance
		movement[period.key]=flt(pl+a+l, 3)
		beginning_balance=beginning_balance+movement[period.key]
		total[period.key] = beginning_balance
	data.append(movement)
	data.append(sa)
	data.append(total)
	return data

def get_net_profit_loss(income, expense, period_list):

	net_profit_loss = {
		"account_name": _("Profit and Loss"),
		"account": None,
		"warn_if_negative": True
	}
	#today=getdate(nowdate())
	#trace=""
	for period in period_list:
		i=0
		e=0
		if income:
			i=income[-2][period.key]
		if expense:
			e=expense[-2][period.key]
		#trace+= ">> {} < {} is {} <<".format(today,period.from_date,today < period.from_date)
		#if today < period.from_date:
		#	net_profit_loss[period.key] = 0
		#else:
		net_profit_loss[period.key] = flt(i-e, 3)
	#frappe.throw(trace)
	return net_profit_loss



def get_period_list(fiscal_year, periodicity, from_beginning=False):
	"""Get a list of dict {"to_date": to_date, "key": key, "label": label}
		Periodicity can be (Yearly, Quarterly, Monthly)"""

	fy_start_end_date = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"])
	if not fy_start_end_date:
		frappe.throw(_("Fiscal Year {0} not found.").format(fiscal_year))

	start_date = getdate(fy_start_end_date[0])
	end_date = getdate(fy_start_end_date[1])

	if periodicity == "Yearly":
		period_list = [_dict({"to_date": end_date, "key": fiscal_year, "label": fiscal_year})]
	else:
		months_to_add = {
			"Half-yearly": 6,
			"Quarterly": 3,
			"Monthly": 1
		}[periodicity]

		period_list = []

		# start with first day, so as to avoid year to_dates like 2-April if ever they occur
		to_date = get_first_day(start_date)
		today=getdate(nowdate())
		for i in xrange(12 / months_to_add):
			if to_date<today:
				to_date = add_months(to_date, months_to_add)
				
				if to_date == get_first_day(to_date):
				# if to_date is the first day, get the last day of previous month
					to_date = add_days(to_date, -1)
				else:
				# to_date should be the last day of the new to_date's month
					to_date = get_last_day(to_date)
	
				if to_date <= end_date:
				# the normal case
					period_list.append(_dict({ "to_date": to_date }))

					# if it ends before a full year
					if to_date == end_date:
						break

				else:
				# if a fiscal year ends before a 12 month period
					period_list.append(_dict({ "to_date": end_date }))
					break

	# common processing
	for opts in period_list:
		key = opts["to_date"].strftime("%b_%Y").lower()
		label = formatdate(opts["to_date"], "MMM YYYY")
		opts.update({
			"key": key.replace(" ", "_").replace("-", "_"),
			"label": label,
			"year_start_date": start_date,
			"year_end_date": end_date
		})

		opts["from_date"] = start_date

	return period_list


def get_data(company, root_type, balance_must_be, period_list, account_list, ignore_closing_entries=False):
	accounts = get_accounts(company, root_type)
	
	if not accounts:
		return None
	isasset=root_type=="Asset"
	
	accounts, accounts_by_name = filter_accounts(accounts)
	gl_entries_by_account = get_gl_entries(company, period_list[0]["from_date"], period_list[-1]["to_date"],
		accounts[0].lft, accounts[0].rgt, account_list,isasset, ignore_closing_entries=ignore_closing_entries)

	calculate_values(accounts, gl_entries_by_account, period_list)
	
	accumulate_values_into_parents(accounts, accounts_by_name, period_list)
	out = prepare_data(accounts, balance_must_be, period_list)

	if out:
		add_total_row(out, balance_must_be, period_list)

	return out

def calculate_values(accounts, gl_entries_by_account, period_list):
	for d in accounts:
		for name in ([d.name] + (d.collapsed_children or [])):
			for entry in gl_entries_by_account.get(name, []):
				sd=None
				for period in period_list:
					if sd==None:
						sd=period.from_date
					entry.posting_date = getdate(entry.posting_date)

					# check if posting date is within the period
					if entry.posting_date <= period.to_date and entry.posting_date > sd:
						d[period.key] = d.get(period.key, 0.0) + flt(entry.debit) - flt(entry.credit)
					sd=period.to_date

def accumulate_values_into_parents(accounts, accounts_by_name, period_list):
	"""accumulate children's values in parent accounts"""
	for d in reversed(accounts):
		if d.parent_account:
			for period in period_list:
				accounts_by_name[d.parent_account][period.key] = accounts_by_name[d.parent_account].get(period.key, 0.0) + d.get(period.key, 0.0)

def prepare_data(accounts, balance_must_be, period_list):
	out = []
	year_start_date = period_list[0]["year_start_date"].strftime("%Y-%m-%d")
	year_end_date = period_list[-1]["year_end_date"].strftime("%Y-%m-%d")

	for d in accounts:
		# add to output
		has_value = False
		row = {
			"account_name": d.account_name,
			"account": d.name,
			"parent_account": d.parent_account,
			"indent": flt(d.indent),
			"from_date": year_start_date,
			"to_date": year_end_date
		}
		for period in period_list:
			if d.get(period.key):
				# change sign based on Debit or Credit, since calculation is done using (debit - credit)
				d[period.key] *= (1 if balance_must_be=="Debit" else -1)

			row[period.key] = flt(d.get(period.key, 0.0), 3)

			if abs(row[period.key]) >= 0.005:
				# ignore zero values
				has_value = True

		if has_value:
			out.append(row)

	return out

def add_total_row(out, balance_must_be, period_list):
	row = {
		"account_name": _("Total ({0})").format(balance_must_be),
		"account": None
	}
	for period in period_list:
		row[period.key] = out[0].get(period.key, 0.0)
		out[0][period.key] = ""

	out.append(row)

	# blank row after Total
	out.append({})

def get_accounts(company, root_type):
	# root lft, rgt
	root_account = frappe.db.sql("""select lft, rgt from `tabAccount`
		where company=%s and root_type=%s order by lft limit 1""",
		(company, root_type), as_dict=True)

	if not root_account:
		return None

	lft, rgt = root_account[0].lft, root_account[0].rgt

	accounts = frappe.db.sql("""select * from `tabAccount`
		where company=%(company)s and lft >= %(lft)s and rgt <= %(rgt)s order by lft""",
		{ "company": company, "lft": lft, "rgt": rgt }, as_dict=True)
	
	return accounts

def filter_accounts(accounts, depth=10):
	parent_children_map = {}
	accounts_by_name = {}
	for d in accounts:
		accounts_by_name[d.name] = d
		parent_children_map.setdefault(d.parent_account or None, []).append(d)

	filtered_accounts = []
	def add_to_list(parent, level):
		if level < depth:
			for child in (parent_children_map.get(parent) or []):
				child.indent = level
				filtered_accounts.append(child)
				add_to_list(child.name, level + 1)

		else:
			# include all children at level lower than the depth
			parent_account = accounts_by_name[parent]
			parent_account["collapsed_children"] = []
			for d in accounts:
				if d.lft > parent_account.lft and d.rgt < parent_account.rgt:
					parent_account["collapsed_children"].append(d.name)

	add_to_list(None, 0)

	return filtered_accounts, accounts_by_name

def get_gl_entries(company, from_date, to_date, root_lft, root_rgt, account_list,isasset, ignore_closing_entries=False):
	"""Returns a dict like { "account": [gl entries], ... }"""
	additional_conditions = []

	if ignore_closing_entries:
		additional_conditions.append("and ifnull(voucher_type, '')!='Period Closing Voucher'")

	if from_date:
		additional_conditions.append("and posting_date >= %(from_date)s")
	addcon=""
	if isasset:
		addcon=" and account NOT IN ({}) ".format(account_list)
	
	gl_entries = frappe.db.sql("""select * from `tabGL Entry`
		where company=%(company)s
		{additional_conditions}
		and posting_date <= %(to_date)s
		and account in (select name from `tabAccount`
			where lft >= %(lft)s and rgt <= %(rgt)s) {addcon} 
		order by account, posting_date""".format(additional_conditions="\n".join(additional_conditions),addcon=addcon),
		{
			"company": company,
			"from_date": from_date,
			"to_date": to_date,
			"lft": root_lft,
			"rgt": root_rgt
		},
		as_dict=True)

	gl_entries_by_account = {}
	for entry in gl_entries:
		gl_entries_by_account.setdefault(entry.account, []).append(entry)

	return gl_entries_by_account

def get_columns(period_list):
	columns = [{
		"fieldname": "account",
		"label": _("Account"),
		"fieldtype": "Link",
		"options": "Account",
		"width": 300
	}]
	for period in period_list:
		columns.append({
			"fieldname": period.key,
			"label": period.label,
			"fieldtype": "Currency",
			"width": 150
		})

	return columns

