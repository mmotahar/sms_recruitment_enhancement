# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    ebay_id = fields.Char('eBay User ID')
