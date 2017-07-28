# -*- coding: utf-8 -*-
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2017 ThinkOpen Solutions (<https://tkobr.com>).
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='# of Sales Order', stored=True)

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        return super(ResPartner, self)._compute_sale_order_count()
