# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero
import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = 'stock.picking'

    # auto assign lots from pack
    # if the product is stockable and tracing is serial
    @api.multi
    def auto_assign_stock_moves(self):
        self.do_unreserve()
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
        self.button_validate()
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


class StockQuant(models.Model):
    _inherit = "stock.quant"

    # ################################################################
    # Inhiert only to not raise the warning
    # this doesn't let module to work
    # odoo always creats stock.moves but we want with our serial numbers
    # ##############################################################
    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                  strict=False):
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=strict)
        available_quantity = self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                                          owner_id=owner_id, strict=strict)
        if float_compare(quantity, 0, precision_rounding=rounding) > 0 and float_compare(quantity, available_quantity,
                                                                                         precision_rounding=rounding) > 0:
            _logger.warning(_('It is not possible to reserve more products of %s than you have in stock.') % (
                ', '.join(quants.mapped('product_id').mapped('display_name'))))
            return []
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0 and float_compare(abs(quantity), sum(
                quants.mapped('reserved_quantity')), precision_rounding=rounding) > 0:
            _logger.warning(_('It is not possible to unreserve more products of %s than you have in stock.') % (
                ', '.join(quants.mapped('product_id').mapped('display_name'))))
            return []

        reserved_quants = []
        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity,
                                                                                     precision_rounding=rounding):
                break
        return reserved_quants