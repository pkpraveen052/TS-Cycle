# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.osv import expression


class StockQuantityHistory(models.TransientModel):
    _name = 'stock.quantity.history'
    _description = 'Stock Quantity History'

    inventory_datetime = fields.Datetime('Inventory at Date',
        help="Choose a date to get the inventory at that date",
        default=fields.Datetime.now)
    use_move_inventory_report_date = fields.Boolean(
        string='Use Stock Move Report Date',
        help="Enable this option to compute the inventory report using the custom report date set on stock moves.",
    )

    def open_at_date(self):
        tree_view_id = self.env.ref('stock.view_stock_product_tree').id
        form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
        domain = [('type', '=', 'product')]
        product_id = self.env.context.get('product_id', False)
        product_tmpl_id = self.env.context.get('product_tmpl_id', False)
        if product_id:
            domain = expression.AND([domain, [('id', '=', product_id)]])
        elif product_tmpl_id:
            domain = expression.AND([domain, [('product_tmpl_id', '=', product_tmpl_id)]])
        # We pass `to_date` in the context so that `qty_available` will be computed across
        # moves until date.
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Products'),
            'res_model': 'product.product',
            'domain': domain,
            'context': dict(
                self.env.context,
                to_date=self.inventory_datetime,
                use_move_inventory_report_date=self.use_move_inventory_report_date,
            ),
        }
        return action
