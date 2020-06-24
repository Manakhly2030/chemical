import frappe, erpnext
from frappe import msgprint, _
from frappe.utils import nowdate, flt, cint, cstr,now_datetime
from erpnext.stock.stock_ledger import update_entries_after
import json

# Utils Overrides
@frappe.whitelist()
def get_incoming_rate(args, raise_error_if_no_rate=True):
	"""Get Incoming Rate based on valuation method"""
	frappe.msgprint('finbyz get_incoming_rate_')
	from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
	from erpnext.stock.utils import get_fifo_rate, get_avg_purchase_rate, get_valuation_method
	from erpnext.stock.stock_ledger import get_previous_sle
	from six import string_types

	if isinstance(args, string_types):
		args = json.loads(args)

	in_rate = 0
	#finbyz changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))
	# finbyz changes
	def get_batch_rate(args):
		"""Get Batch Valuation Rate of Batch No"""
		
		item_code = args.get('item_code')
		batch_no = args.get('batch_no')

		conditions = f"and item_code = '{item_code}' and batch_no = '{batch_no}' "
		
		if args.get("warehouse"):
			warehouse = args.get("warehouse")
			conditions += f" and warehouse = '{warehouse}' "

		if args.get("company"):
			company =  args.get("company")
			conditions += f" and company = '{company}' "

		return flt(frappe.db.sql(f"""SELECT incoming_rate FROM `tabStock Ledger Entry` 
			WHERE actual_qty > 0 and docstatus = 1 {conditions}""")[0][0])

	#finbyz changes
	if args.get("batch_no") and batch_wise_cost:
		in_rate = get_batch_rate(args)
		#frappe.msgprint(f"inside:{in_rate}")

	elif (args.get("serial_no") or "").strip():
		in_rate = get_avg_purchase_rate(args.get("serial_no"))
	
	else:
		valuation_method = get_valuation_method(args.get("item_code"))
		previous_sle = get_previous_sle(args)
		if valuation_method == 'FIFO':
			if previous_sle:
				previous_stock_queue = json.loads(previous_sle.get('stock_queue', '[]') or '[]')
				in_rate = get_fifo_rate(previous_stock_queue, args.get("qty") or 0) if previous_stock_queue else 0
		elif valuation_method == 'Moving Average':
			in_rate = previous_sle.get('valuation_rate') or 0

	if not in_rate:
		voucher_no = args.get('voucher_no') or args.get('name')
		in_rate = get_valuation_rate(args.get('item_code'), args.get('warehouse'),
			args.get('voucher_type'), voucher_no, args.get('allow_zero_valuation'),
			currency=erpnext.get_company_currency(args.get('company')), company=args.get('company'),
			raise_error_if_no_rate=raise_error_if_no_rate)

	#frappe.msgprint(str(in_rate))

	return in_rate


# Stock Ledger Overides

def process_sle(self, sle):
	#frappe.msgprint("Process SLE Called")
	self.allow_negative_stock = cint(frappe.db.get_single_value("Stock Settings",
				"allow_negative_stock"))
	if (sle.serial_no and not self.via_landed_cost_voucher) or not cint(self.allow_negative_stock):
		# validate negative stock for serialized items, fifo valuation
		# or when negative stock is not allowed for moving average
		if not update_entries_after.validate_negative_stock(self,sle):
			self.qty_after_transaction += flt(sle.actual_qty)
			return

	# Finbyz Changes
	batch_wise_cost = cint(frappe.db.get_single_value("Stock Settings", 'exact_cost_valuation_for_batch_wise_items'))
	if sle.batch_no and batch_wise_cost:
		get_batch_values(self,sle)
		self.qty_after_transaction += flt(sle.actual_qty)
		self.stock_value = flt(self.qty_after_transaction) * flt(self.valuation_rate)
	
	elif sle.serial_no:
		# Finbyz Changes end
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
	item_code = cstr(sle.item_code)
	conditions = f"and item_code = '{item_code}' and batch_no = '{batch_no}' "

	if sle.get("warehouse"):
		warehouse = sle.get("warehouse")
		conditions += f" and warehouse = '{warehouse}' "

	if sle.get("company"):
		company =  sle.get("company")
		conditions += f" and company = '{company}' "

	if incoming_rate < 0:
		# wrong incoming rate
		incoming_rate = self.valuation_rate

	stock_value_change = 0
	if incoming_rate:
		stock_value_change = actual_qty * incoming_rate
		
	elif actual_qty < 0:
		# In case of delivery/stock issue, get average purchase rate
		# of serial nos of current entry
		stock_value_change = actual_qty * flt(frappe.db.sql(f"""SELECT incoming_rate FROM `tabStock Ledger Entry` 
	WHERE actual_qty > 0 and docstatus = 1 {conditions}""")[0][0])

	new_stock_qty = self.qty_after_transaction + actual_qty

	if new_stock_qty > 0:
		new_stock_value = (self.qty_after_transaction * self.valuation_rate) + stock_value_change
		if new_stock_value >= 0:
			# calculate new valuation rate only if stock value is positive
			# else it remains the same as that of previous entry
			self.valuation_rate = new_stock_value / new_stock_qty

	if not self.valuation_rate and sle.voucher_detail_no:
		allow_zero_rate = update_entries_after.check_if_allow_zero_valuation_rate(sle.voucher_type, sle.voucher_detail_no)
		if not allow_zero_rate:
			self.valuation_rate = get_valuation_rate(sle.item_code, sle.warehouse,
				sle.voucher_type, sle.voucher_no, self.allow_zero_rate,
				currency=erpnext.get_company_currency(sle.company))

# Stock Entry Overrides

def get_args_for_incoming_rate(self, item):
	frappe.msgprint('get_args_for_incoming_rate')
	return frappe._dict({
		"item_code": item.item_code,
		"warehouse": item.s_warehouse or item.t_warehouse,
		"posting_date": self.posting_date,
		"posting_time": self.posting_time,
		"qty": item.s_warehouse and -1*flt(item.transfer_qty) or flt(item.transfer_qty),
		"serial_no": item.serial_no,
		"voucher_type": self.doctype,
		"voucher_no": self.name,
		"company": self.company,
		"allow_zero_valuation": item.allow_zero_valuation_rate,
		"batch_no": item.batch_no, # FinByz Changes
	})

# Buying Controller overrides
def update_raw_materials_supplied_based_on_bom(self, item, raw_material_table):
	frappe.msgprint('update_raw_materials_supplied_based_on_bom')
	from erpnext.controllers.buying_controller import get_items_from_bom
	from erpnext.stock.doctype.stock_entry.stock_entry import get_used_alternative_items
	from erpnext.stock.stock_ledger import get_valuation_rate

	exploded_item = 1
	if hasattr(item, 'include_exploded_items'):
		exploded_item = item.get('include_exploded_items')

	bom_items = get_items_from_bom(item.item_code, item.bom, exploded_item)

	used_alternative_items = []
	if self.doctype == 'Purchase Receipt' and item.purchase_order:
		used_alternative_items = get_used_alternative_items(purchase_order = item.purchase_order)

	raw_materials_cost = 0
	items = list(set([d.item_code for d in bom_items]))
	item_wh = frappe._dict(frappe.db.sql("""select i.item_code, id.default_warehouse
		from `tabItem` i, `tabItem Default` id
		where id.parent=i.name and id.company=%s and i.name in ({0})"""
		.format(", ".join(["%s"] * len(items))), [self.company] + items))

	for bom_item in bom_items:
		if self.doctype == "Purchase Order":
			reserve_warehouse = bom_item.source_warehouse or item_wh.get(bom_item.item_code)
			if frappe.db.get_value("Warehouse", reserve_warehouse, "company") != self.company:
				reserve_warehouse = None

		conversion_factor = item.conversion_factor
		if (self.doctype == 'Purchase Receipt' and item.purchase_order and
			bom_item.item_code in used_alternative_items):
			alternative_item_data = used_alternative_items.get(bom_item.item_code)
			bom_item.item_code = alternative_item_data.item_code
			bom_item.item_name = alternative_item_data.item_name
			bom_item.stock_uom = alternative_item_data.stock_uom
			conversion_factor = alternative_item_data.conversion_factor
			bom_item.description = alternative_item_data.description

		# check if exists
		exists = 0
		for d in self.get(raw_material_table):
			if d.main_item_code == item.item_code and d.rm_item_code == bom_item.item_code \
				and d.reference_name == item.name:
					rm, exists = d, 1
					break

		if not exists:
			rm = self.append(raw_material_table, {})

		required_qty = flt(flt(bom_item.qty_consumed_per_unit) * (flt(item.qty) + getattr(item, 'rejected_qty', 0)) *
			flt(conversion_factor), rm.precision("required_qty"))
		rm.reference_name = item.name
		rm.bom_detail_no = bom_item.name
		rm.main_item_code = item.item_code
		rm.rm_item_code = bom_item.item_code
		rm.stock_uom = bom_item.stock_uom
		rm.required_qty = required_qty
		if self.doctype == "Purchase Order" and not rm.reserve_warehouse:
			rm.reserve_warehouse = reserve_warehouse

		rm.conversion_factor = conversion_factor

		if self.doctype in ["Purchase Receipt", "Purchase Invoice"]:
			rm.consumed_qty = required_qty
			rm.description = bom_item.description
			if item.batch_no and frappe.db.get_value("Item", rm.rm_item_code, "has_batch_no") and not rm.batch_no:
				rm.batch_no = item.batch_no

		# get raw materials rate
		if self.doctype == "Purchase Receipt":
			from erpnext.stock.utils import get_incoming_rate
			rm.rate = get_incoming_rate({
				"item_code": bom_item.item_code,
				"warehouse": self.supplier_warehouse,
				"posting_date": self.posting_date,
				"posting_time": self.posting_time,
				"qty": -1 * required_qty,
				"serial_no": rm.serial_no,
				"batch_no": rm.batch_no #FinByz Changes
			})
			if not rm.rate:
				rm.rate = get_valuation_rate(bom_item.item_code, self.supplier_warehouse,
					self.doctype, self.name, currency=self.company_currency, company = self.company)
		else:
			rm.rate = bom_item.rate

		rm.amount = required_qty * flt(rm.rate)
		raw_materials_cost += flt(rm.amount)

	if self.doctype in ("Purchase Receipt", "Purchase Invoice"):
		item.rm_supp_cost = raw_materials_cost

def append_raw_material_to_be_backflushed(self, fg_item_doc, raw_material_data, qty):
	rm = self.append('supplied_items', {})
	rm.update(raw_material_data)

	rm.required_qty = qty
	rm.consumed_qty = qty

	if not raw_material_data.get('non_stock_item'):
		from erpnext.stock.utils import get_incoming_rate
		rm.rate = get_incoming_rate({
			"item_code": raw_material_data.rm_item_code,
			"warehouse": self.supplier_warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			"qty": -1 * qty,
			"serial_no": rm.serial_no,
			"batch_no": rm.batch_no #FinByz Changes
		})

		if not rm.rate:
			rm.rate = get_valuation_rate(raw_material_data.item_code, self.supplier_warehouse,
				self.doctype, self.name, currency=self.company_currency, company=self.company)

	rm.amount = qty * flt(rm.rate)
	fg_item_doc.rm_supp_cost += rm.amount

# Selling Controller Overrides
def update_stock_ledger(self):
	frappe.msgprint('update_stock_ledger')
	from erpnext.controllers.selling_controller import SellingController
	from erpnext.controllers.stock_controller import StockController
	from erpnext.stock.get_item_details import get_conversion_factor
	from erpnext.stock.stock_ledger import make_sl_entries
	
	SellingController.update_reserved_qty(self)

	sl_entries = []
	for d in self.get_item_list():
		if frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1 and flt(d.qty):
			if flt(d.conversion_factor)==0.0:
				d.conversion_factor = get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0
			return_rate = 0
			if cint(self.is_return) and self.return_against and self.docstatus==1:
				return_rate = self.get_incoming_rate_for_sales_return(d.item_code, self.return_against)

			# On cancellation or if return entry submission, make stock ledger entry for
			# target warehouse first, to update serial no values properly

			if d.warehouse and ((not cint(self.is_return) and self.docstatus==1)
				or (cint(self.is_return) and self.docstatus==2)):
					sl_entries.append(self.get_sl_entries(d, {
						"actual_qty": -1*flt(d.qty),
						"incoming_rate": return_rate
					}))

			if d.target_warehouse:
				target_warehouse_sle = self.get_sl_entries(d, {
					"actual_qty": flt(d.qty),
					"warehouse": d.target_warehouse
				})

				if self.docstatus == 1:
					if not cint(self.is_return):
						args = frappe._dict({
							"item_code": d.item_code,
							"warehouse": d.warehouse,
							"posting_date": self.posting_date,
							"posting_time": self.posting_time,
							"qty": -1*flt(d.qty),
							"serial_no": d.serial_no,
							"company": d.company,
							"voucher_type": d.voucher_type,
							"voucher_no": d.name,
							"allow_zero_valuation": d.allow_zero_valuation,
							"batch_no": d.batch_no # FinByz Changes
						})
						target_warehouse_sle.update({
							"incoming_rate": get_incoming_rate(args)
						})
					else:
						target_warehouse_sle.update({
							"outgoing_rate": return_rate
						})
				sl_entries.append(target_warehouse_sle)

			if d.warehouse and ((not cint(self.is_return) and self.docstatus==2)
				or (cint(self.is_return) and self.docstatus==1)):
					sl_entries.append(self.get_sl_entries(d, {
						"actual_qty": -1*flt(d.qty),
						"incoming_rate": return_rate
					}))
	make_sl_entries(sl_entries)