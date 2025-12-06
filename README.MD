# Accounting for esun Sate (nasin nanpa mani pi esun Sate)

[esun Sate](https://esun.sadale.net/) is an informal store created by jan Sate (Sadale) operating on non-profit basis.

This repo records the accounting and inventory information of esun Sate. The ultimate purpose is to calculate the profit with reasonable accuracy so that giveaways can be performed while making sure that jan Sate wouldn't be losing money in the operation.

jan Sate commits free labor for delivering at least first 30 units of devices per year across all his hardware projects. He does not foresee the demand would sustainably go beyond that.

## View Latest Financial Record

Please view the latest record here: [./output.txt](./output.txt)

## Usage

Run `analyzer.py` to obtain the statistics of esun Sate

## Example

Please see `record-example.csv` for how the operation are recorded. It includes an example of recording of assembled units, direct shipment, a batched US shipment, and a giveaway. It also has the sample output of `analyzer.py` showing the profit and cashflow at the end.

## Parameter format:

* DATE format: `YYYY-MM-DD`
* REF (Order Number) format:
	* YYYYMMDD_N, where N is the order number of that date
	* Each order number can contain suborders such as 20251101_0a or 20251101_0b. The suffix is just a syntactic sugar with no meaning to the script itself
* BATCH format: a number. It can has alphabet suffix to be used as subbatch number. The suffix is just a syntactic sugar with no meaning to the script itself

## Giveaway Handling

For esun Sate:

* The definition of "Cash Flow" is all of the income minus all of the expense minus all of the fees.
* The definition of "Profit" is all of the income minus the expense of the consumed units (sold units, units kept for R&D, giveaway units, etc.) minus all of the fees of such incomes and expenses. Whenever a unit is assembled, a unit price is calculated and whenever a unit is RESERVE'D or RELEASE'D, the expense would be incurred against the "Profit".
* The "Profit" is always higher than "Cash Flow" because the expense is immediately incurred to the "Cash Flow" when the money is paid, and it's only incurred to the "Profit" when the unit in the inventory is released. Meanwhile, the income is always immediately registered on both "Profit" and "Cash Flow" The delayed application of the expense to the "Profit" makes it higher than the "Cash Flow".
* Giveaway would happen upon occurance of either of the follows:
	* the "Profit" is high enough to cover the warranty/repair requests and I'm confident that the remaining units in the inventory can be sold in a reasonably timeframe
	* the "Cash Flow" is high enough to cover the warranty/repair requests

## Limitations:

* Doesn't track inventory of material. It only track the inventory of assembled units.
* The unit cost of each batch is an approximation. Since extra material are always ordered just in case, some of the cost of next batch may be counted toward to the previous batch
* Floating point arithematics rounding error - it's negligible and I wouldn't mind being off by a few cents.
* For material coming from taobao, I only create an entry for each shipment to Hong Kong SAR. The RMB exchange rate might change between the moment I make the purchase of the material and the moment that I pay for the shipping fee. For simplicity, only the exchange rate at the date of payment of shipping fee is recorded.
* Supporting documents are not commited to the git repo to avoid sensitive info from being accidentally included, in which I wouldn't be able to remove

## Accounting method:

* Expense of equipment: If the equipment is specific to the project, full price would be counted toward the project. If it's shared by the project, at most half of the price of the equipment would be counted.
* Expense of material shipping: I often purchase personal stuffs on taobao unrelated to the esun Sate projects along with the esun Sate's material, consolidate them and ship all the stuffs to Hong Kong SAR in one-go.  If the shipment is dedicated to the project's material, full shipping price would be counted. If the shipment is predominantly other stuffs unrelated to the project, the shipment fee would not be counted. Otherwise, half of the shipping fee would be counted.
* Fee of all taobao expenses are fixed at 3% to account for transaction fee and currency exchange loss.
* Fee of all Paypal expenses are fixed at 3% to account for currency conversion loss upon I convert the fund from HKD to USD.
* Credit card payment fee to JLCPCB is fixed at 2% to account to account for transaction fee and currency conversion loss.
* Income from Paypal has a fixed fee of 3% on top of whatever existing seller fee might be in place to account for currency conversion loss when I withdraw it as HKD.
* In addition to giveaways, sometimes I might gift a unit of my product to my friends. If whoever I'm gifting to is not a significant contributor of toki pona community nor a contributor of my projects, I will pay for the unit out of my own wallet at cost price. Example that I would pay for: Gifting a unit for exhibition in hackerspace, gifting to my close friends for sharing. Example that I won't pay for: gifting to volunteers that help on the project(s), a unit kept for my own R&D use.
* ilo nanpa donation pool handling: TBC

## Receipts

* All receipts are uploaded here with annotations for the public to perform audit of the record.csv: [lipu mani pi esun Sate](https://esun.sadale.net/lipumani/)
* Redacted information for protecting the privacy of the recipients and myself: transaction ID, shipping tracking numbers, recipient's name, shipping addresses

## Calculation of Unit Cost of each Batch

1. Run python with -i against analyzer.py so that I'd get to the REPL after the script ends
2. Run the following command for obtaining the total cost of ilonena BATCH 1: `round(sum([i["VALUE"] for i in data_table if i["ACTION"] == "EXPENSE" and i["PROJECT"] == "ilonena" and i["TYPE"] == "material" and remove_suffix(i["BATCH"])]), 3)`
3. Manually divide the above value with the quantity of the batch to obtain the material cost
