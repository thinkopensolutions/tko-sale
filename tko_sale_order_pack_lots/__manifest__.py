# -*- encoding: utf-8 -*-

{
    'name': 'tko_sale_order_pack_lots',
    'version': '11.0',
    'category': 'customization',
    'sequence': 150,
    'complexity': 'normal',
    'description': '''  This module creates a pack and adds on SOL
      which allows to add multiple serial numbers in same sale order line''',
    'author': 'ThinkOpen Solutions Brasil',
    'website': 'http://www.tkobr.com',
    'images': [
        'images/oerp61.jpeg',
    ],
    'depends': [
        'stock',
        'sale',
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/serial_pack_data.xml',
        'views/sale_serial_pack_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
    ],
    'init': [],
    'demo': [],
    'update': [],
    'test': [],  # YAML files with tests
    'installable': True,
    'application': False,
    'auto_install': False,
    'certificate': '',
}
