#!/usr/bin/python3

# Copyright 2025 Wong Cho Ching <https://sadale.net>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import datetime
import json
import re
import os
import sys
import urllib.request

if len(sys.argv) < 3:
	print(f"Usage: {sys.argv[0]} <record.csv> <exchange-rate-cache-dir>")
	exit(1)

RECORD_PATH = sys.argv[1]
EXCHANGE_RATE_CACHE_PATH = sys.argv[2]

def convert_to_usd(date, amount):
	amount = amount.strip()
	if amount == "0":
		currency = "USD"
		amount_value = 0
	else:
		matches = re.match("([A-Za-z]{3})([0-9.]+)", amount)
		if matches is None:
			raise ValueError(f"Invalid currency format: {amount}")
		currency = matches.group(1)
		amount_value = float(matches.group(2))

	# Special handling for RMB: Replace it with CNY
	if currency == "RMB":
		currency = "CNY"

	cache_file = os.path.join(EXCHANGE_RATE_CACHE_PATH, f"{date}.json")
	if not os.path.exists(cache_file):
		r = urllib.request.urlopen(f"https://api.frankfurter.dev/v1/{date}?base=USD")
		with open(cache_file, 'wb') as f:
			f.write(r.read())

	with open(cache_file) as f:
		exchange_rate = json.load(f)

	if currency.upper() == "USD":
		return amount_value

	if currency.upper() not in exchange_rate["rates"]:
		raise ValueError(f"Invalid currency: {currency.upper()}")

	return amount_value / exchange_rate["rates"][currency.upper()]


def compute_value(date, amount, fee, income):
	amount_value = convert_to_usd(date, amount)
	if fee.endswith("%"):
		fee_value = amount_value * float(fee[:-1]) / 100.0
	else:
		fee_value = convert_to_usd(date, fee)

	# Expense - Deduct fee from the amonut
	if income:
		return amount_value - fee_value
	# Expense - Add fee to the amonut
	return amount_value + fee_value

def parse_items(items):
	ret = {}
	for item in items.split():
		matches = re.match("([A-Za-z]+)([0-9]+)", item)
		if matches is None:
			raise ValueError("Invalid ITEMS vaule: {items}")
		ret[matches.group(1)] = int(matches.group(2))
	return ret

def remove_suffix(s):
	return re.match("([0-9-_]+)[A-Za-z]*", s).group(1) if s != "" else ""

AVAILABLE_ACTIONS = {
	"OBTAIN": {"required": ["DATE", "TYPE", "PROJECT", "QUANTITY", "COSTEACH"], "optional": ["BATCH", "REMARKS"]},
	"RESERVE": {"required": ["DATE", "REF", "ITEMS"], "optional": ["REMARKS"]},
	"RELEASE": {"required": ["DATE", "TYPE", "REF", "ITEMS"], "optional": ["REMARKS"]},
	"INCOME": {"required": ["DATE", "TYPE", "AMOUNT", "FEE"], "optional": ["REF", "REMARKS"]},
	"EXPENSE": {"required": ["DATE", "TYPE", "AMOUNT", "FEE"], "optional": ["PROJECT", "BATCH", "SUPPLIER", "REF", "REMARKS"]},
}
# Remarks: "VALUE" is automatically computed from "AMOUNT" and "FEE"

AVAILABLE_TYPES = {
	"OBTAIN": ["assembled", "returned", "repaired"],
	"RELEASE": ["sales", "gift", "replacement", "giveaway", "scrap"],
	"INCOME": ["sales", "donation"],
	"EXPENSE": ["R&D", "material", "shipping", "replacement", "reimbursement", "refund"],
}

# List of available projects
AVAILABLE_ITEMS = ["ilonena", "ilomusiali"]

# Pass 1 - parse fields into data table
data_table = []
with open(RECORD_PATH) as f:
	for line in f.readlines():
		line = line.replace('\n', '')
		if not line or line.startswith("#"):
			continue
		action, fields = line.split(':', 1)
		if "REMARKS" in fields:
			remarks_index = fields.find("REMARKS")
			remarks_content = fields[remarks_index:]
			fields = [i.strip() for i in fields[:remarks_index].split(',') if i.strip()]
			fields.append(remarks_content)
		else:
			fields = [i.strip() for i in fields.split(',')]
		data_table.append({"ACTION": action} | {i.split(' ',1)[0].strip():i.split(' ',1)[1].strip() for i in fields})

# Pass 2 - Data Validation, fill in optional fields and perform currency conversions
last_date = "0000-00-00"
for line in data_table:
	######################
	# Stage A validation #
	######################
	# Validate action
	action = line["ACTION"]
	if action not in AVAILABLE_ACTIONS:
		raise ValueError(f"Invalid action: {line}")

	# Validate if all require fields exists
	for required_field in AVAILABLE_ACTIONS[action]["required"]:
		if required_field not in line:
			raise ValueError(f"Missing field {required_field} in this line: {line}")

	# Validate date
	matches = re.match("([0-9]{4})-([0-9]{2})-([0-9]{2})", line["DATE"])
	if matches is None:
		raise ValueError(f"Wrong DATE format in this line: {line}")
	try:
		datetime.datetime(int(matches.group(1)), int(matches.group(2)), int(matches.group(3)))
	except ValueError:
		raise ValueError(f"Wrong DATE value in this line: {line}")

	if line["DATE"] < last_date:
		raise ValueError(f"Non-chronological date found: {line}")
	last_date = line["DATE"]

	# Validate type
	if "TYPE" in line and line["TYPE"] not in AVAILABLE_TYPES[action]:
		raise ValueError(f"Invalid TYPE value in this line: {line}")

	# Validate project names
	if "PROJECT" in line and line["PROJECT"] not in AVAILABLE_ITEMS:
		raise ValueError(f"Invalid PROJECT value in this line: {line}")

	# Validate items names
	if "ITEMS" in line and sum([0 if i in AVAILABLE_ITEMS else 1 for i in parse_items(line["ITEMS"])]):
		raise ValueError(f"Invalid ITEMS value in this line: {line}")

	# Fill optional fields if not provided (must be done after finishing stage A validation because they don't account for empty fields)
	for optional_field in AVAILABLE_ACTIONS[action]["optional"]:
		if optional_field not in line:
			line[optional_field] = ""

	for field in line:
		if field not in ["ACTION"] + AVAILABLE_ACTIONS[action]["required"] + AVAILABLE_ACTIONS[action]["optional"]:
			raise ValueError(f"Unrecognized field {field}: {line}")

	##############################################
	# Stage B validation and currency conversion #
	##############################################
	if "COSTEACH" in line:
		try:
			line["COSTEACH"] = convert_to_usd(line["DATE"], line["COSTEACH"])
		except Exception as e:
			raise ValueError(f"Invalid currency in the following line: {line}")

	if "QUANTITY" in line:
		try:
			line["QUANTITY"] = int(line["QUANTITY"])
		except Exception as e:
			raise ValueError(f"Invalid qualtity value in the following line: {line}")

	if action == "INCOME":
		line["VALUE"] = compute_value(line["DATE"], line["AMOUNT"], line["FEE"], income=True)
	elif action == "EXPENSE":
		line["VALUE"] = compute_value(line["DATE"], line["AMOUNT"], line["FEE"], income=False)

	##############################
	# Stage C special validation #
	##############################
	if action == "EXPENSE" and line["TYPE"] == "material" and (len(line["PROJECT"]) == 0 or len(line["BATCH"]) == 0 or len(line["SUPPLIER"]) == 0):
		raise ValueError(f"Must have PROJECT, BATCH and SUPPLIER for material: {line}")
	
	

# Pass 3 - Compute total income/expense and stats
item_cost = {p:[] for p in AVAILABLE_ITEMS} # FIFO item cost for each unit. The key is the PROJECT's name, and the value is a list of each item.
ref_value = {'':0.0}
reserved_items_counter = {} # The amonut of items that has been RESERVE'd but not RELEASE'd
cash_flow = 0.0 # income/expense of the fund spend/received at this moment
profit = 0.0 # income/expense of the stock that has been consumed (the material cost isn't counted until consumed)

def add_reserved_inventory(ref, items, remarks):
	total = 0.0
	items = parse_items(items)
	for item_name, quantity in items.items():
		if ref not in reserved_items_counter:
			reserved_items_counter[ref] = {"items": {}, "remarks": remarks if not None else ""}
		reserved_items_counter[ref]["items"][item_name] = quantity

def take_reserved_inventory(ref, items):
	total = 0.0
	items = parse_items(items)
	for item_name, quantity in items.items():
		reserved_items_counter[ref]["items"][item_name] -= quantity
		if reserved_items_counter[ref]["items"][item_name] == 0:
			reserved_items_counter[ref]["items"].pop(item_name)
		elif reserved_items_counter[ref]["items"][item_name] < 0:
			raise ValueError(f"Attempting to RELEASE more items than it has from RESERVE'd items. REF: {ref}")

def items_to_str(item_dict):
	return ','.join([f"{name}{quantity}" for name, quantity in item_dict.items()])


def take_item_and_compute_cost(items):
	total = 0.0
	items = parse_items(items)
	for item_name, quantity in items.items():
		for unit in range(quantity):
			total += item_cost[item_name][0]
			item_cost[item_name] = item_cost[item_name][1:]
	return total

for line in data_table:
	action = line["ACTION"]
	if action == "INCOME":
		ref_value[remove_suffix(line["REF"])] += line["VALUE"]
		cash_flow += line["VALUE"]
		profit += line["VALUE"]
	elif action == "EXPENSE":
		cash_flow -= line["VALUE"]
		if line["TYPE"] != "material":
			ref_value[remove_suffix(line["REF"])] -= line["VALUE"]
			profit -= line["VALUE"]
		else:
			# For material, deduct it during RESERVE or RELEASE
			pass
	elif action == "OBTAIN":
		item_cost[line["PROJECT"]] += [line["COSTEACH"]] * line["QUANTITY"]
	elif action == "RESERVE":
		if remove_suffix(line["REF"]) in ref_value:
			raise Exception(f"Duplicated RESERVE REF: {line}")
		item_value = take_item_and_compute_cost(line["ITEMS"])
		add_reserved_inventory(remove_suffix(line["REF"]), line["ITEMS"], line.get("REMARKS"))
		ref_value[remove_suffix(line["REF"])] = -item_value
		profit -= item_value
	elif action == "RELEASE":
		# Remove item from inventory and deduct the cost if it hasn't already been RESERVE'D
		if remove_suffix(line["REF"]) not in reserved_items_counter:
			item_value = take_item_and_compute_cost(line["ITEMS"])
			if remove_suffix(line["REF"]) not in ref_value:
				ref_value[remove_suffix(line["REF"])] = 0.0
			ref_value[remove_suffix(line["REF"])] -= item_value
			profit -= item_value
		else:
			take_reserved_inventory(remove_suffix(line["REF"]), line["ITEMS"])

print("Breakdown of profit of all orders:")
for i in sorted(ref_value):
	print(f"{(i if i else 'NOREF\t')}\t{ref_value[i]:.2f} USD")
print("----------")
print(f"Profit:\t\t{profit:.2f} USD (does not include material cost of inventory that hasn't been consumed)")
print(f"Cash Flow:\t{cash_flow:.2f} USD (includes material cost of inventory that hasn't been consumed)")
print("----------")
print("Inventory (Does not include the ones already sent to the US warehouse):")
for i in sorted(item_cost):
	print(f"{i}\t{len(item_cost[i])}\tNext unit @{item_cost[i][0] if len(item_cost[i]) > 0 else 'N/A'} USD")
print("Reserved units (Counted towards consumed inventory):")
for i in sorted(reserved_items_counter):
	if len(reserved_items_counter[i]["items"]) != 0:
		print(f"{i}\t{items_to_str(reserved_items_counter[i]['items'])}\t{reserved_items_counter[i]['remarks']}")
