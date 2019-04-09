from odoo import api, fields, models


class Survey(models.Model):
    _inherit = 'survey.survey'

    @api.multi
    def action_print_survey(self):
        """ Override function to open survey in new tab"""
        """ Open the website page with the survey printable view """
        self.ensure_one()
        token = self.env.context.get('survey_token')
        trail = "/" + token if token else ""
        return {
            'type': 'ir.actions.act_url',
            'name': "Print Survey",
            'target': '_blank',
            'url': self.with_context(relative_url=True).print_url + trail
        }

    @api.multi
    def action_result_survey(self):
        """ Override function to open survey results in new tab"""
        """ Open the website page with the survey results view """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Survey",
            'target': '_blank',
            'url': self.with_context(relative_url=True).result_url
        }

    @api.multi
    def action_test_survey(self):
        """ Override function to open survey test in new tab
            Open the website page with the survey form into test mode
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': "Results of the Survey",
            'target': '_blank',
            'url': self.with_context(relative_url=True).public_url + "/phantom"
        }
