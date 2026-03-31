from odoo import fields, models
from odoo.tools.float_utils import float_round


class Product(models.Model):
    _inherit = 'product.product'

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        if not self.env.context.get('use_move_inventory_report_date'):
            return super()._compute_quantities_dict(lot_id, owner_id, package_id, from_date=from_date, to_date=to_date)

        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        dates_in_the_past = False
        to_date = fields.Datetime.to_datetime(to_date)
        if to_date and to_date < fields.Datetime.now():
            dates_in_the_past = True

        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)

        from_date_value = fields.Date.to_date(from_date) if from_date else from_date
        to_date_value = fields.Date.to_date(to_date) if to_date else to_date
        if from_date:
            date_domain_from = [('inventory_report_date', '>=', from_date_value)]
            domain_move_in += date_domain_from
            domain_move_out += date_domain_from
        if to_date:
            date_domain_to = [('inventory_report_date', '<=', to_date_value)]
            domain_move_in += date_domain_to
            domain_move_out += date_domain_to

        Move = self.env['stock.move'].with_context(active_test=False)
        Quant = self.env['stock.quant'].with_context(active_test=False)
        domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        quants_res = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in Quant.read_group(domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
        if dates_in_the_past:
            domain_move_in_done = [('state', '=', 'done'), ('inventory_report_date', '>', to_date_value)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('inventory_report_date', '>', to_date_value)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

        res = {}
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            if not product_id:
                res[product_id] = dict.fromkeys(['qty_available', 'free_qty', 'incoming_qty', 'outgoing_qty', 'virtual_available'], 0.0)
                continue
            rounding = product.uom_id.rounding
            if dates_in_the_past:
                qty_available = quants_res.get(product_id, [0.0])[0] - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
            else:
                qty_available = quants_res.get(product_id, [0.0])[0]
            reserved_quantity = quants_res.get(product_id, [False, 0.0])[1]
            res[product_id] = {
                'qty_available': float_round(qty_available, precision_rounding=rounding),
                'free_qty': float_round(qty_available - reserved_quantity, precision_rounding=rounding),
                'incoming_qty': float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding),
                'outgoing_qty': float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding),
            }
            res[product_id]['virtual_available'] = res[product_id]['qty_available'] + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty']

        return res
