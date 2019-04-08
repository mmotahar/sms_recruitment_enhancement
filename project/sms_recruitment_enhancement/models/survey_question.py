# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    question_attachment = fields.Binary('Question attachment')
    type = fields.Selection([
        ('free_text', 'Multiple Lines Text Box'),
        ('textbox', 'Single Line Text Box'),
        ('numerical_box', 'Numerical Value'),
        ('date', 'Date'),
        ('upload_file', 'Upload file'),
        ('simple_choice', 'Multiple choice: only one answer'),
        ('multiple_choice', 'Multiple choice: multiple answers allowed'),
        ('matrix', 'Matrix')],
        string='Type of Question', default='free_text', required=True)

    @api.multi
    def validate_upload_file(self, post, answer_tag):
        self.ensure_one()
        errors = {}
        answer = post[answer_tag]
        # Empty answer to mandatory question
        if self.constr_mandatory and not answer:
            errors.update({answer_tag: self.constr_error_msg})
        return errors
