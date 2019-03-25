# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    ebay_id = fields.Char('eBay User ID')

    def _find_existing_address(self, address_data):
        """ address_data should be a dict representing an address
            return the first address that matches address_data
        """
        for addr in self | self.child_ids:
            if addr._compare_addresses(address_data):
                return addr
        return False

    def _compare_addresses(self, address_data):
        """ address_data should be a dict representing an address
            return true if the two addresses are essentially the same
        """
        def normalize(string):
            # to minimize the number of duplicates this could be more aggressive
            return string.lower() if string else ''
        address_char_fields = ['street', 'street2', 'city', 'zip', 'name', 'phone']
        address_rel_fields = ['state_id', 'country_id']
        for field in address_char_fields:
            if normalize(self[field]) != normalize(address_data[field]):
                return False
        for field in address_rel_fields:
            if (self[field].id if self[field] else 0) != address_data[field]:
                return False
        return True
