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
