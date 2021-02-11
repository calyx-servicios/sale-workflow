# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sale Order Attachment Status",
    "summary": """
        This module purpose is to show in Sale Order List View 
        if the record that has attachments.""",
    "author": "Calyx Servicios S.A.",
    "maintainers": ["FedericoGregori"],
    "website": "http://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    "category": "Sales",
    "version": "11.0.1.0.0",
    # see https://odoo-community.org/page/development-status
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    # any module necessary for this one to work correctly
    "depends": ["base", "sale"],
    # always loaded
    "data": [
        "views/sale_order_view.xml",
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
