# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    # auto assign lots from pack
    # if the product is stockable and tracing is serial
    @api.multi
    def auto_assign_stock_moves(self):
        for line in self.move_lines:
            for lot in line.pack_id.pack_ids:
                if line.product_id.type == 'product' and line.product_id.tracking == 'serial':
                    self.env['stock.move.line'].create({'lot_id': lot.lot_id.id,
                                                        'product_id': line.product_id.id,
                                                        'product_uom_qty': 1,
                                                        'product_uom_id': line.product_uom.id,
                                                        'location_id': line.location_id.id,
                                                        'location_dest_id': line.location_dest_id.id,
                                                        'move_id': line.id,
                                                        'picking_id': line.picking_id.id,
                                                        'qty_done': 1,
                                                        })
                    # set lot reserved
                    lot.lot_id.reserve_lot()
        self.action_assign()
        try:
            # try to validate if serial numers are correct,
            # should validate
            self.button_validate()
        except:
            pass
        return True


class StockMove(models.Model):
    _inherit = "stock.move"

    pack_id = fields.Many2one('serial.number.pack', u'Pack')

    # set serial number reserved on adding move line
    # directly
    @api.multi
    def write(self, vals):
        result = super(StockMove, self).write(vals)
        for record in self:
            for line in record.move_line_ids:
                line.lot_id.reserve_lot = True
        return result


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.multi
    def unlink(self):
        for record in self:
            if record.lot_id:
                record.lot_id.unreserve_lot()
        return super(StockMoveLine, self).unlink()


class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    serial_reserved = fields.Selection([('r', u'Reserved'), ('u', u'Un Reserved')], default='u', required=True,
                                       string=u'Reserved?')

    def reserve_lot(self):
        print("called reserve lot.........")
        self.serial_reserved = 'r'

    def unreserve_lot(self):
        print("called un-reserve lot.........")
        self.serial_reserved = 'u'
