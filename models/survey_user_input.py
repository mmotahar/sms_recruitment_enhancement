# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    @api.multi
    def create_applicant(self):
        self.ensure_one()
        # Get some info from survey submission to create application
        survey_id = self.survey_id and self.survey_id.id or False
        job = self.env['hr.job'].search(
            [('survey_id', '=', survey_id)], limit=1)
        basic_info = {}
        for uil in self.user_input_line_ids:
            for info in ['Full Name', 'Email Address', 'Contact Number',
                         'Address']:
                if uil.question_id and uil.question_id.question == info:
                    value = uil.value_text \
                        if info != 'Address' else uil.value_free_text
                    basic_info.update({info: value})
        self.env['hr.applicant'].create({
            'name': job and job.name or '',
            'partner_name': basic_info.get('Full Name', False),
            'email_from': basic_info.get('Email Address', False),
            'partner_phone': basic_info.get('Contact Number', False),
            'job_id': job and job.id or False,
        })
        return True

    @api.multi
    def write(self, vals):
        res = super(SurveyUserInput, self).write(vals)
        if vals.get('state', False) == 'done':
            self.create_applicant()
        return res

    @api.model
    def create(self, vals):
        res = super(SurveyUserInput, self).create(vals)
        if not res.deadline:
            # When the applicant start survey, the deadline
            # is set from now plus 14 days
            res.deadline = datetime.now() + relativedelta(days=14)
        return res
