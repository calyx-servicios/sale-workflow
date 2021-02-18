from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    attachment_status = fields.Char(string="Attachments")
