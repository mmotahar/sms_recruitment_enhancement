# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class IrActionsReport(models.Model):
    _name = 'ir.actions.report'
    _inherit = ['studio.mixin', 'ir.actions.report']

    @api.model
    def render_qweb_html(self, docids, data=None):
        if data and data.get('full_branding'):
            self = self.with_context(full_branding=True)
        return super(IrActionsReport, self).render_qweb_html(docids, data)

    def copy_report_and_template(self):
        new = self.copy()
        view = self.env['ir.ui.view'].search([
            ('type', '=', 'qweb'),
            ('key', '=', new.report_name),
        ])
        view.ensure_one()
        new_view = view.with_context(lang=None).copy_qweb_template()
        copy_no = int(new_view.key.split('_copy_').pop())

        new.write({
            'xml_id': '%s_copy_%s' % (new.xml_id, copy_no),
            'name': '%s copy(%s)' % (new.name, copy_no),
            'report_name': '%s_copy_%s' % (new.report_name, copy_no),
            'report_file': new_view.key,  # TODO: are we sure about this?
        })
