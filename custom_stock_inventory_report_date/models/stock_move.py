from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_report_date = fields.Date(
        string='Inventory Report Date',
        index=True,
        help='Custom date used by inventory history reporting when enabled from the quantity history wizard.',
    )
