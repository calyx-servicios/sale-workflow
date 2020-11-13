from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    

    container_ids = fields.One2many('sale.container', 'sale_order_id', string='Container Lines',)


    
    @api.multi
    def cancel_container_move(self):
        for order in self:
            for container in order.container_ids:
                container.action_cancel()

    @api.multi
    def create_container_move(self):
        for order in self:
            for container in order.container_ids:
                if container.state=='draft':
                    container.action_open()

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()
        self.create_container_move()
        return res

 
    @api.multi
    def action_cancel(self):
        res = super(SaleOrder,self).action_cancel()
        container_res=self.cancel_container_move()
        return res

    

    
    @api.model
    def create(self, vals):
        racks=0
        container=0
        if vals.get('racks', False):
            racks=vals.get('racks')
        if vals.get('container', False):
            container=vals.get('container')
        if racks<0 or container<0:
            raise ValidationError(_('Rack and Container values cant be negatives'))
        return super(SaleOrder,self).create(vals)

    def set_containers(self):
        
                
            return {    
                'name': _("Containers"),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.container.wizard',
                'target': 'new',
                
            }
        
    