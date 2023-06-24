from frappe import _

def get_data():
	return {
		'fieldname': 'reference_name',
		'non_standard_fieldnames': {
			'Quality Inspection': 'reference_name',
			'Product Research': 'inward_sample'
		},
		'transactions': [
			{	
				'label': _('Quality Inspection'),
				'items': ['Quality Inspection']
			},	
			{	
				'label': _('Product Research'),
				'items': ['Product Research']
			},	
		]
	}