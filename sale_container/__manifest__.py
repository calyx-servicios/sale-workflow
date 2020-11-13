# -*- coding: utf-8 -*-
{
    'name': "Sale Container",
    'summary': """
        Sales Containers """,

    'description': """
        
    """,
    'author': "Calyx",
    'website': "http://www.calyxservicios.com.ar",
    'category': 'Sales',
    'version': '0.1',
    'depends' : [
        'base_setup', 
        'base', 
        'sale'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/container_return_view.xml',
        'wizard/sale_container_wizard.xml',
        'views/sale_order_view.xml',
        'views/product_view.xml',
        'wizard/simple_return_wizard.xml',
        'views/sale_container_view.xml',
        'report/container_template.xml',
        'report/container_report.xml',
        'report/return_template.xml',
        'report/return_report.xml',
        'views/menu.xml',
    ],
}