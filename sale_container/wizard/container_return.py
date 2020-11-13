from odoo import models, api, fields, _
from ast import literal_eval
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class SaleContainerReturnLine(models.TransientModel):
    _name = 'sale.container.return.line'
    _description = 'Sale Container Return Line Wizard'
   
    return_id = fields.Many2one('sale.container.return', string='Return')
    return_line_id = fields.Many2one('sale.container.line', string='Line',readonly=True)
    sale_container_id = fields.Many2one('sale.container', string='Container',readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    product_id = fields.Many2one('product.product', domain=[('container_ok', '=', True)], string='Bill',readonly=True)
    quantity = fields.Integer(string='Quantity',readonly=True)
    remain_quantity = fields.Integer(string='Remain Quantity',readonly=True)
    returned_quantity = fields.Integer(string='Return Quantity')
    

class SaleContainerReturn(models.TransientModel):

    _name = 'sale.container.return'
    _description = 'Sale Container Return Wizard'

    
    @api.model
    def _default_lines(self):
        _logger.debug('========context=======%r',self._context)
        _logger.debug('========get default lines====== %r', self._context.get('active_ids'))
        container_obj = self.env['sale.container']
        container_line_obj = self.env['sale.container.line']
        lines = []
        if self._context.get('default_res_model') and self._context.get('default_res_model')=='res.partner':
            partner_id=self._context.get('default_res_id')
            for line in container_line_obj.search([('partner_id','=',partner_id),('state','=','open')]):
                    if line.remain_quantity>0 or line.state == 'open':
                        lines.append({'product_id':line.product_id.id,
                            'quantity':line.quantity,
                            'remain_quantity':line.remain_quantity,
                            'return_line_id': line.id,
                            'partner_id': line.sale_container_id.partner_id.id,
                            'sale_container_id': line.sale_container_id.id,
                            'returned_quantity':line.remain_quantity})
        else:
            for container in container_obj.browse(self._context.get('active_ids')):
                for line in container.line_ids:
                    if line.remain_quantity>0 or line.state == 'open':
                        lines.append({'product_id':line.product_id.id,
                            'quantity':line.quantity,
                            'remain_quantity':line.remain_quantity,
                            'return_line_id': line.id,
                            'partner_id': line.sale_container_id.partner_id.id,
                            'sale_container_id': container.id,
                            'returned_quantity':line.remain_quantity})
        _logger.debug('=====Return wizards default lines====%r',lines)
        return lines

    line_ids = fields.One2many('sale.container.return.line', 'return_id', string='Lines',default=_default_lines)

    @api.multi
    def do_return(self):
        container_ids=[]
        receive_obj = self.env['sale.container.receive']
        receive_line_obj = self.env['sale.container.receive.line']
        line_ids={}
        for container_return in self: 
            for line in container_return.line_ids:
                if line.returned_quantity>0:
                    if line.return_line_id.sale_container_id.partner_id.id not in line_ids:
                        line_ids.setdefault(line.return_line_id.sale_container_id.partner_id.id,[])
                    line_ids[line.return_line_id.sale_container_id.partner_id.id].append(line)
                    if line.returned_quantity>line.return_line_id.remain_quantity:
                        line.returned_quantity=line.return_line_id.remain_quantity
                    line.return_line_id.returned_quantity=line.return_line_id.returned_quantity+line.returned_quantity
        _logger.debug('===== do_return lines====%r',line_ids)
        if len(line_ids)>0:
            for partner, lines in line_ids.items():
                receive_id=receive_obj.create({'partner_id':partner})
                _logger.debug('===== return receive created====%r:%r',receive_id, partner, lines)
                for line in lines:
                    line_data={
                            'receive_id': receive_id.id,
                            'return_line_id': line.return_line_id.id,
                            'quantity':line.returned_quantity}
                    line_id=receive_line_obj.create(line_data)
                receive_id.action_close()
                if self._context.get('default_res_model') and self._context.get('default_res_model')=='res.partner':
                    return self.print(receive_id)
    
    @api.multi
    def print(self, receive):
        _logger.debug('=======Print======')
        self.ensure_one()
        
        action=self.env['ir.actions.report']._get_report_from_name('sale_container.report_sale_container_receive').report_action(receive)
        return action
        
    

            
            

