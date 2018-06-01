from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SerialNumberPack(models.Model):
    _name = 'serial.number.pack'

    name = fields.Char(u'Name', readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('serial.number.pack') or _('New'))
    product_id = fields.Many2one('product.product', u'Product')
    pack_ids = fields.One2many('serial.number.pack.line', 'pack_id', 'Lots')

    @api.constrains('pack_ids')
    def validate_pack_ids(self):
        lots = self.pack_ids.mapped('lot_id').ids
        if len(lots) != len(self.pack_ids):
            raise  UserError(_("Duplicate serial numbers selected in pack %s" %self.name))


class SalePackSerialNumbersLine(models.Model):
    _name = 'serial.number.pack.line'

    pack_id = fields.Many2one('serial.number.pack', 'Pack')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')

    @api.multi
    def unlink(self):
        for record in self:
            if record.lot_id:
                record.lot_id.unreserve_lot()
        return super(SalePackSerialNumbersLine, self).unlink()
