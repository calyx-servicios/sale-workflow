from odoo import models, api, fields, _
from ast import literal_eval
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class SaleContainerWizardLine(models.TransientModel):
    _name = 'sale.container.wizard.line'
    _description = 'Sale Container Wizard Line'
   
    wizard_id = fields.Many2one('sale.container.wizard', string='Wizard')
    state = fields.Selection([('draft', 'Draft'),('open', 'Open'),('close', 'Close'),('cancel', 'Cancel')], string='State',default='draft')
    line_id = fields.Many2one('sale.container.line', string='Line',readonly=True)
    sale_container_id = fields.Many2one('sale.container', string='Container',readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    product_id = fields.Many2one('product.product', domain=[('container_ok', '=', True)], string='Product')
    quantity = fields.Integer(string='Quantity',states={'draft': [('readonly', False)]},)
    remain_quantity = fields.Integer(string='Remain Quantity',readonly=True)
    returned_quantity = fields.Integer(string='Return Quantity',states={'draft': [('readonly', False)]},)
    

class SaleContainerWizard(models.TransientModel):

    _name = 'sale.container.wizard'
    _description = 'Sale Container Wizard'

    @api.model
    def _default_order(self):
        if self._context.get('active_ids'):
            return self._context.get('active_ids')[0]

    @api.model
    def _default_lines(self):
        _logger.debug('========get default lines====== %r', self._context.get('active_ids'))
        sale_obj = self.env['sale.order']
        lines = []
        for sale in sale_obj.browse(self._context.get('active_ids')):
            if sale.container_ids:
                for container in sale.container_ids:
                    for line in container.line_ids:
                        lines.append({
                            'product_id':line.product_id.id,
                            'quantity':line.quantity,
                            'remain_quantity':line.remain_quantity,
                            'line_id': line.id,
                            'partner_id': line.sale_container_id.partner_id.id,
                            'sale_container_id': line.sale_container_id.id,
                            'state':line.sale_container_id.state,
                            'returned_quantity':line.remain_quantity})
        if len(lines)<=0:
            product_obj = self.env['product.product']
            for product in product_obj.search([('container_ok','=',True)]):
                _logger.debug('========get default line====== %r', product.id)
                lines.append({
                    'product_id':product.id,
                    'quantity':1,
                    'remain_quantity':0,
                    'returned_quantity':0})
        
        return lines

    line_ids = fields.One2many('sale.container.wizard.line', 'wizard_id', string='Lines', default=_default_lines)
    order_id = fields.Many2one("sale.order", string="Order", readonly=True, default=_default_order)


    @api.multi
    def set_container(self):
        line_obj=self.env['sale.container.line']
        container_obj=self.env['sale.container']
        lines = []
        must=False
        for wiz in self: 
            for line in wiz.line_ids:
                if line.quantity>0 and line.product_id:
                    must=True
            if must:
    
                open_container=False
                for line in wiz.line_ids:
                    if line.line_id and line.line_id.sale_container_id.state=='draft':
                        open_container=line.line_id.sale_container_id.id

                for line in wiz.line_ids:
                    if line.line_id:
                        if line.line_id.sale_container_id and line.line_id.sale_container_id.state=='draft':
                                line.line_id.quantity=line.quantity
                    else:
                        if line.product_id.id and line.quantity>0:
                            if not open_container:
                                vals={
                                    'sale_order_id' : wiz.order_id.id,
                                    'partner_id' : wiz.order_id.partner_id.id,
                                    'line_ids': False
                                }
                                open_container=container_obj.create(vals).id

                            line_vals={
                                'sale_container_id':open_container,
                                'product_id':line.product_id.id,
                                'quantity': line.quantity,
                                'partner_id' : wiz.order_id.partner_id.id
                            }
                            line_obj.create(line_vals)
                        
                            
        
        
                
    
    

