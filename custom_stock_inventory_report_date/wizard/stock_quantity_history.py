from odoo import fields, models


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    use_move_inventory_report_date = fields.Boolean(
        string='Use Stock Move Report Date',
        help='Enable this option to compute the inventory report using the custom report date set on stock moves.',
    )

    def open_at_date(self):
        action = super().open_at_date()
        action['context'] = dict(
            action.get('context', {}),
            use_move_inventory_report_date=self.use_move_inventory_report_date,
        )
        return action
