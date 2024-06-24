from frappe import _

def get_data():
	return {
		'fieldname': 'outward_sample',
		"internal_links": {
			"Quality Inspection": ["items", "outward_sample"],
			"Quotation": ["items", "outward_sample"],
		},
		'transactions': [
			{	
				'label': _('Quality Inspection'),
				'items': ['Quality Inspection']
			},
				{	
				'label': _('Quotation'),
				'items': ['Quotation']
			},
		]
	}