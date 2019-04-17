from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
from odoo import api, fields, models


class SurveyMailComposeMessage(models.TransientModel):
    _inherit = 'survey.mail.compose.message'

    @api.model
    def _get_default_deadline(self):
        # deadline = today + 14
        return datetime.now().date() + relativedelta(days=14)

    date_deadline = fields.Date(
        default=lambda self: self._get_default_deadline()
    )
    public = fields.Selection(default='email_public_link')

    @api.multi
    @api.onchange('public')
    def _onchange_public(self):
        for record in self:
            if record.public == 'public_link':
                record.public = 'email_public_link'
                raise Warning('You should not share the public link. '
                              'Please invite by email')
