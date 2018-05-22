# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Unlink lots on cancelling orders
    @api.multi
    def action_cancel(self):
        for record in self:
            for line in record.order_line:
                line.pack_id.pack_ids.unlink()
        return super(SaleOrder, self).action_cancel()

    # call method to auto assign move lines on order confirmation
    @api.multi
    def _action_confirm(self):
        lot_obj = self.env['stock.production.lot']
        res = super(SaleOrder, self)._action_confirm()
        ## set pack and lots on order
        assign = False
        for record in self:
            for line in record.order_line:
                # break for loop if qty and serial numbers are matched
                if int(line.product_uom_qty) == len(line.pack_id.pack_ids) or not line.pack_id:
                    continue
                assign = True
                ### unlink lots before linking again
                line.pack_id.pack_ids.unlink()
                if line.pack_id:
                    if record.warehouse_id and line.product_id:
                        location = record.warehouse_id.lot_stock_id
                        quants = self.env['stock.quant'].read_group([
                            ('product_id', '=', line.product_id.id),
                            ('location_id', 'child_of', location.id),
                            ('quantity', '>', 0),
                            ('lot_id', '!=', False),
                        ], ['lot_id'], 'lot_id')
                        ## reverse list and pop the last element
                        available_lot_ids = [quant['lot_id'][0] for quant in quants][::-1]
                    # filter serial_reserved lots
                    for lot_id in available_lot_ids:
                        lot = lot_obj.browse(lot_id)
                        if lot.serial_reserved == 'r' or lot.product_qty < 1:
                            available_lot_ids.remove(lot_id)
                    if len(available_lot_ids) < int(line.product_uom_qty):
                        raise Warning("Not enough lots available for pack %s" % line.pack_id.name)
                    # link lots to serial numbers
                    for i in range(0, int(line.product_uom_qty)):
                        self.env['serial.number.pack.line'].create({
                            'pack_id': line.pack_id.id,
                            'lot_id': available_lot_ids[-1]
                        })
                        # pop last serail number
                        available_lot_ids.pop()

        # must get picking here to auto assign
        if assign:
            for order in self:
                picking = order.picking_ids.filtered(
                    lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
                if not picking.picking_type_id.use_existing_lots or picking.picking_type_id.use_create_lots:
                    picking.picking_type_id.use_existing_lots = False
                    picking.picking_type_id.use_create_lots = False
                picking.auto_assign_stock_moves()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pack_id = fields.Many2one('serial.number.pack', u'Pack', copy=False)

    @api.model
    def create(self, vals):
        result = super(SaleOrderLine, self).create(vals)
        if result.product_id.type == 'product' and result.product_id.tracking == 'serial':
            pack = self.env['serial.number.pack'].create({'product_id': vals['product_id']})
            result.pack_id = pack.id
        return result
