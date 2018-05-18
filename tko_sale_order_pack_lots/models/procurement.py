# -*- coding: utf-8 -*-

from odoo import models, fields,  api, _

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'


    # set pack_id in move lines
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if 'sale_line_id' in values:
            sol = self.env['sale.order.line'].browse(values['sale_line_id'])
            if sol.pack_id:
                result.update({'pack_id': sol.pack_id.id})
        return result