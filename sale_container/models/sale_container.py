from odoo import models, api, fields, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class SaleContainerLine(models.Model):
    _name = 'sale.container.line'
    _description = 'Sales Container Line'

    @api.model
    def create(self, vals):
        if vals.get('quantity', 0)<=0:
            raise ValidationError(_('Quantity Must be Positive'))
        return super(SaleContainerLine, self).create(vals)
    
    @api.model
    def write(self, vals):
        if vals.get('quantity') and vals.get('quantity')<=0:
            raise ValidationError(_('Quantity Must be Positive'))
        return super(SaleContainerLine, self).write(vals)

   

    sale_container_id = fields.Many2one('sale.container', string='Sale Container',ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', domain=[('container_ok', '=', True)], change_default=True, ondelete='restrict', required=True,states={'draft': [('readonly', False)]})
    return_ids = fields.One2many('sale.container.receive.line', 'return_line_id', help='Technical: used to compute returned quantities.')
    quantity = fields.Integer(string='Quantity',default=1,states={'draft': [('readonly', False)]})
    returned_quantity = fields.Integer(string='Returned Quantity',compute='_compute_returned', readonly=True)
    remain_quantity = fields.Integer(string='Remain Quantity',compute='_compute_remain',readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company',  
        default=lambda self: self.env['res.company']._company_default_get('sale.container'), readonly=True, related_sudo=False)
    partner_id = fields.Many2one("res.partner", related='sale_container_id.partner_id', string="Partner", readonly=True, store=True)
    user_id = fields.Many2one("res.users", related='sale_container_id.user_id', string="User", readonly=True, store=True)
    state = fields.Selection([('draft', 'Draft'),('open', 'Open'),('close', 'Close'),('cancel', 'Cancel')], string='State',default='draft')

    @api.depends('quantity','return_ids.quantity','return_ids','state','sale_container_id.state')
    def _compute_returned(self):
        res = {}
        for line in self:
            
            return_qty= 0
            for _return in line.return_ids:
                if _return.receive_id.state in ['close']:
                    return_qty+=_return.quantity
            
            line.returned_quantity = return_qty
        
    
    @api.depends('quantity','return_ids.quantity','return_ids','state','sale_container_id.state')
    def _compute_remain(self):
        res = {}
        for line in self:
            
            return_qty= 0
            for _return in line.return_ids:
                if _return.receive_id.state in ['close']:
                    return_qty+=_return.quantity
            line.remain_quantity = line.quantity-return_qty
    


class SaleContainer(models.Model):
    _name = 'sale.container'
    _description = 'Sales Container'
    _inherit = ['mail.thread']

    @api.model
    def _default_partner(self):
        active_id=self._context.get('active_id')
        if active_id:
            return self.env['sale.order'].browse(active_id).partner_id.id

    @api.model
    def _default_sale(self):
        active_id=self._context.get('active_id')
        return active_id

    @api.model
    def _default_lines(self):
        product_obj = self.env['product.product']
        lines = []
        for product in product_obj.search([('container_ok','=',True)]):
                    lines.append({'product_id':product.id,
                        'quantity':1,
                        'remain_quantity':1,
                        'returned_quantity':0})
        return lines

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', default=_default_sale)
    date_container = fields.Datetime(string='Container Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Partner', domain=[('customer', '=', True)], 
        states={'draft': [('readonly', False)]},ondelete='restrict', required=True, default=_default_partner)
    line_ids = fields.One2many('sale.container.line', 'sale_container_id', string='Container Lines',states={'draft': [('readonly', False)]},default=_default_lines)
    user_id = fields.Many2one('res.users',  string="User Create", states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company',  
        default=lambda self: self.env['res.company']._company_default_get('sale.container'), readonly=True, related_sudo=False)
    state = fields.Selection([('draft', 'Draft'),('open', 'Open'),('close', 'Close'),('cancel', 'Cancel')], string='State',default='draft')
    note = fields.Text('Terms and conditions',)


    @api.multi
    def unlink(self):
        for container in self:
            if container.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete a Container which is not draft or cancelled. You should cancel it first.'))
        return super(SaleContainer, self).unlink()
                    

    @api.model
    def create(self, vals):
        if vals.get('sale_order_id') and not vals.get('partner_id'):
            sale = self.env['sale.order'].browse(vals.get('sale_order_id'))
            vals['partner_id']=sale.partner_id.id
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.container') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.container') or _('New')
        return super(SaleContainer, self).create(vals)

    # @api.model
    # def write(self, vals):
        
    #     _logger.debug('=====write sale container===%r',vals)
    #     if vals.get('sale_order_id') and not vals.get('partner_id'):
    #         sale = self.env['sale.order'].browse(vals.get('sale_order_id'))
    #         vals['partner_id']=sale.partner_id.id
    #     res = super(SaleContainer, self).write(vals)
    #     return res


    @api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
        })

    @api.multi
    def action_cancel(self):
        for container in self:
            returns_open=False
            for line in container.line_ids:
                for _return in line.return_ids:
                    _logger.debug('=====check cancel firsr====%r',_return.return_id.state)
                    if _return.receive_id.state not in ['draft','cancel']:
                        returns_open=True
            if not returns_open:
                for line in container.line_ids:
                    line.state='cancel'
                self.state='cancel'
            else:
                raise UserError(_('You cannot cancel a Container With Returns Opended. You should cancel the Returns first.'))


    @api.multi
    def action_open(self):
        for container in self:
            for line in container.line_ids:
                line.state='open'
        return self.write({'state': 'open'})

    @api.multi
    def action_close(self):
        for container in self:
            for line in container.line_ids:
                line.state='close'
        return self.write({'state': 'close'})

    @api.multi
    def action_return(self):
        for container in self:
            for line in container.line_ids:
                line.returned_quantity=line.quantity
                line.state='close'
        return self.write({'state': 'close'})

    


class SaleContainerReceiveLine(models.Model):
    _name = 'sale.container.receive.line'
    _description = 'Sale Container Return Line Wizard'
   
    receive_id = fields.Many2one('sale.container.receive', string='Return',ondelete='cascade')
    return_line_id = fields.Many2one('sale.container.line', string='Line',readonly=True)
    return_id = fields.Many2one("sale.container", related='return_line_id.sale_container_id',string="Container", readonly=True)
    partner_id = fields.Many2one("res.partner", related='return_line_id.sale_container_id.partner_id',string="Partner", readonly=True)
    sale_container_id = fields.Many2one('sale.container', related='return_line_id.sale_container_id',string='Container')
    product_id = fields.Many2one('product.product', related='return_line_id.product_id', string='Product',readonly=True)
    quantity = fields.Integer(string='Quantity',readonly=True)
    

class SaleContainerReceive(models.Model):

    _name = 'sale.container.receive'
    _description = 'Sale Container Receive'
    partner_id = fields.Many2one("res.partner", string="Partner", readonly=True)
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Draft'),('open', 'Open'),('close', 'Close'),('cancel', 'Cancel')], string='State',default='draft')

    line_ids = fields.One2many('sale.container.receive.line', 'receive_id', string='Lines')
    date_container = fields.Datetime(string='Container Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users',  string="User Create", states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.container.receive') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.container.receive') or _('New')
        return super(SaleContainerReceive, self).create(vals)

    @api.multi
    def unlink(self):
        for container in self:
            if container.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete a Container Receive which is not draft or cancelled. You should cancel it first.'))
        return super(SaleContainerReceive, self).unlink()


    @api.multi
    def action_close(self):
        container_obj = self.env['sale.container']
        for container in self:
            container_ids=[]
            container.state='close'
            for line in container.line_ids:
                _logger.debug('=====return line?===%r',line)
                if line.sale_container_id and line.sale_container_id.id not in container_ids:
                    container_ids.append(line.sale_container_id.id)

                
                for scontainer in container_obj.browse(container_ids):
                    _logger.debug('=====container to close====%r',scontainer.name)
                    ready=True
                    for line in scontainer.line_ids:
                        if line.remain_quantity>0:
                            ready=False
                        else:
                            line.state='close'
                    if ready:
                        scontainer.action_close()
                
            

    @api.multi
    def action_cancel(self):
        container_obj = self.env['sale.container']
        for container in self:
            container_ids=[]
            for line in container.line_ids:
                line.state='cancel'
                if not line.return_line_id.sale_container_id.id in container_ids:
                    container_ids.append(line.return_line_id.sale_container_id.id)
            container.state='cancel'
         
                

        for container in container_obj.browse(container_ids):
            if container.state=='close':
                container.action_open()
        