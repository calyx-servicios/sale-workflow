from odoo import models, api, fields, _
from ast import literal_eval
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class SaleContainerSimpleWizardLine(models.TransientModel):
    _name = 'sale.container.simple.line'
    _description = 'Sale Container Simple Line'
   
    wizard_id = fields.Many2one('sale.container.simple', string='Wizard')
    product_id = fields.Many2one('product.product', domain=[('container_ok', '=', True)], string='Product')
    quantity = fields.Integer(string='Quantity',readonly=True)
    returned_quantity = fields.Integer(string='Return Quantity')
    

class SaleContainerSimpleWizard(models.TransientModel):

    _name = 'sale.container.simple'
    _description = 'Sale Container Simple'

    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    line_ids = fields.One2many('sale.container.simple.line', 'wizard_id', string='Lines')

    @api.model
    @api.onchange('partner_id')
    def _set_lines(self):
        _logger.debug('========set default lines====== %r', self.partner_id.id)
        container_line_obj = self.env['sale.container.line']
        _line_ids={}
        self.line_ids=False
        for line in container_line_obj.search([('partner_id','=',self.partner_id.id),('state','=','open')]):
            if not line.product_id.id in _line_ids:
                _line_ids.setdefault(line.product_id.id, 0.0)
            _line_ids[line.product_id.id]+=line.remain_quantity
        __line_ids=[]
        for product,qty in _line_ids.items():
                _logger.debug('========set default line====== %r: qty: %r', product, qty)
                __line_ids.append({
                    'product_id':product,
                    'quantity':qty,
                    'returned_quantity':qty})
        self.line_ids=__line_ids
        
        

    @api.multi
    def set_next(self):
        _logger.debug('=======set NEXT Steve Jobs======')
        
        context = self._context.copy()
        
        container_line_obj = self.env['sale.container.line']
        line_ids=container_line_obj.search([('partner_id','=',self.partner_id.id),('state','=','open')])
        if line_ids and len(line_ids)>0:
            context.update({
                'default_res_model':'res.partner',
                'default_res_id': self.partner_id.id,})
            return {    
                    'name': _("Containers"),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sale.container.return',
                    'context': context,
                    'default_res_model':'res.partner',
                    'default_res_id': self.partner_id.id,
                    'target': 'new',
                    
                }
        else:
            raise ValidationError(_('There are not containers to return for this partner!'))

    @api.multi
    def set_return(self):
        _logger.debug('=======set return of jedi======')
        container_line_obj = self.env['sale.container.line']
        counter={}
        receive_obj = self.env['sale.container.receive']
        receive_line_obj = self.env['sale.container.receive.line']
        line_ids={}
        doit=False

        _line_ids={}
        for line in container_line_obj.search([('partner_id','=',self.partner_id.id),('state','=','open')]):
            if not line.product_id.id in _line_ids:
                _line_ids.setdefault(line.product_id.id, 0.0)
            _line_ids[line.product_id.id]+=line.remain_quantity

        for _line in self.line_ids:

            _logger.debug('=======set default for %r:quantity=>%r returned=>%r ',_line.product_id.id, _line.quantity, _line.returned_quantity)
            qty=_line.returned_quantity
            if qty<0:
                raise ValidationError(_('You cant return negative quantities'))
            if qty>_line_ids[_line.product_id.id]:
                qty=_line_ids[_line.product_id.id]
                raise ValidationError(_('You cant return more that remain quantity'))
            if qty>0:
                doit=True
            

            _logger.debug('=======set default for %r:qty:%r',_line.product_id.id,qty)
            counter.setdefault(_line.product_id.id,{'qty':qty,'satisfied':0})
        lines=[]
        if doit:
            receive_id=receive_obj.create({'partner_id':self.partner_id.id})
            for line in container_line_obj.search([('partner_id','=',self.partner_id.id),('state','=','open')]):
                if (line.remain_quantity>0 or line.state == 'open') and line.product_id.id in counter:
                    _logger.debug('=======satisfied for %r:qty=>%r satisfied=>%r',line.product_id.id, counter[line.product_id.id]['qty'], counter[line.product_id.id]['satisfied'])
                    if counter[line.product_id.id]['satisfied']<counter[line.product_id.id]['qty']:
                        needed=counter[line.product_id.id]['qty']-counter[line.product_id.id]['satisfied']
                        take=line.remain_quantity
                        if take>needed:
                            take=needed
                        line_data={
                                    'receive_id': receive_id.id,
                                    'return_line_id': line.id,
                                    'quantity':take}
                        line_id=receive_line_obj.create(line_data)
                        _logger.debug('=======create line receive %r:',line_data)
                        counter[line.product_id.id]['satisfied']+=take
            receive_id.action_close()
            return self.print(receive_id)
    
    @api.multi
    def print(self, receive):
        _logger.debug('=======Print======')
        self.ensure_one()
        
        action=self.env['ir.actions.report']._get_report_from_name('sale_container.report_sale_container_receive').report_action(receive)
        return action
        
    

