import frappe
from frappe.utils import _, cin, flt

def process_sle(self, sle):
	if (sle.serial_no and not self.via_landed_cost_voucher) or not cint(self.allow_negative_stock):
		# validate negative stock for serialized items, fifo valuation
		# or when negative stock is not allowed for moving average
		if not self.validate_negative_stock(sle):
			self.qty_after_transaction += flt(sle.actual_qty)
			return

	# Finbyz Changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))
	if sle.batch_no and batch_wise_cost:
		self.get_batch_values(sle)
		self.qty_after_transaction += flt(sle.actual_qty)
		self.stock_value = flt(self.qty_after_transaction) * flt(self.valuation_rate)
	
	elif sle.serial_no:
		self.get_serialized_values(sle)
		self.qty_after_transaction += flt(sle.actual_qty)
		if sle.voucher_type == "Stock Reconciliation":
			self.qty_after_transaction = sle.qty_after_transaction

		self.stock_value = flt(self.qty_after_transaction) * flt(self.valuation_rate)
	else:
		if sle.voucher_type=="Stock Reconciliation" and not sle.batch_no:
			# assert
			self.valuation_rate = sle.valuation_rate
			self.qty_after_transaction = sle.qty_after_transaction
			self.stock_queue = [[self.qty_after_transaction, self.valuation_rate]]
			self.stock_value = flt(self.qty_after_transaction) * flt(self.valuation_rate)
		else:
			if self.valuation_method == "Moving Average":
				self.get_moving_average_values(sle)
				self.qty_after_transaction += flt(sle.actual_qty)
				self.stock_value = flt(self.qty_after_transaction) * flt(self.valuation_rate)
			else:
				self.get_fifo_values(sle)
				self.qty_after_transaction += flt(sle.actual_qty)
				self.stock_value = sum((flt(batch[0]) * flt(batch[1]) for batch in self.stock_queue))

	# rounding as per precision
	self.stock_value = flt(self.stock_value, self.precision)

	stock_value_difference = self.stock_value - self.prev_stock_value

	self.prev_stock_value = self.stock_value

	# update current sle
	sle.qty_after_transaction = self.qty_after_transaction
	sle.valuation_rate = self.valuation_rate
	sle.stock_value = self.stock_value
	sle.stock_queue = json.dumps(self.stock_queue)
	sle.stock_value_difference = stock_value_difference
	sle.doctype="Stock Ledger Entry"
	frappe.get_doc(sle).db_update()


# Finbyz changes
def get_batch_values(self, sle):
	incoming_rate = flt(sle.incoming_rate)
	actual_qty = flt(sle.actual_qty)
	batch_no = cstr(sle.batch_no)

	if incoming_rate < 0:
		# wrong incoming rate
		incoming_rate = self.valuation_rate

	stock_value_change = 0
	if incoming_rate:
		stock_value_change = actual_qty * incoming_rate
	elif actual_qty < 0:
		# In case of delivery/stock issue, get average purchase rate
		# of serial nos of current entry
		stock_value_change = actual_qty * flt(frappe.db.sql("""select valuation_rate
			from `tabBatch` where name = %s """, batch_no)[0][0])

	new_stock_qty = self.qty_after_transaction + actual_qty

	if new_stock_qty > 0:
		new_stock_value = (self.qty_after_transaction * self.valuation_rate) + stock_value_change
		if new_stock_value >= 0:
			# calculate new valuation rate only if stock value is positive
			# else it remains the same as that of previous entry
			self.valuation_rate = new_stock_value / new_stock_qty

	if not self.valuation_rate and sle.voucher_detail_no:
		allow_zero_rate = self.check_if_allow_zero_valuation_rate(sle.voucher_type, sle.voucher_detail_no)
		if not allow_zero_rate:
			self.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
				sle.voucher_type, sle.voucher_no, self.allow_zero_rate,
				currency=erpnext.get_company_currency(sle.company))
