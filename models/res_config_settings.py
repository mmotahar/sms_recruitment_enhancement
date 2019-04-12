# -*- coding: utf-8 -*-
# Copyright 2009-2018 Trobz (http://trobz.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.tools.safe_eval import safe_eval
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    created_master_data_survey = fields.Boolean(
        string="Created Master Data Survey")

    def get_values(self):
        """
        Read document configurations from system parameter
        """
        res = super(ResConfigSettings, self).get_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        created_master_data_survey = IrConfig.get_param(
            'created_master_data_survey', 'False')
        res.update({
            'created_master_data_survey':
            safe_eval(created_master_data_survey)
        })
        return res

    def set_values(self):
        """
        Update changing configurations to system parameter
        """
        super(ResConfigSettings, self).set_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        for record in self:
            IrConfig.set_param(
                'created_master_data_survey',
                record.created_master_data_survey)
