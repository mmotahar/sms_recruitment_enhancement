# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    answer_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('free_text', 'Free Text'),
        ('upload_file', 'Upload file'),
        ('suggestion', 'Suggestion'),
        ('list', 'List box'),
        ('matrix_models', 'Matrix models')], string='Answer Type')

    file = fields.Binary('Upload file')
    filename = fields.Char(string='Filename', size=256, readonly=True)

    @api.model
    def save_line_upload_file(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'survey_id': question.survey_id.id,
            'skipped': False
        }
        filename = ''
        file = None
        if post[answer_tag]:
            file = base64.encodebytes(post[answer_tag].read())
            filename = post[answer_tag].filename
        if answer_tag in post:
            vals.update({
                'answer_type': 'upload_file',
                'file': file,
                'filename': filename})
        else:
            vals.update({'answer_type': None, 'skipped': True})
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('survey_id', '=', question.survey_id.id),
            ('question_id', '=', question.id)
        ])
        if old_uil:
            old_uil.write(vals)
        else:
            old_uil.create(vals)
        return True
