# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
import logging
import uuid

_logger = logging.getLogger(__name__)


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

    @api.model
    def _create_master_data_survey(self):
        # Check to ensure run this function one time
        IrConfig = self.env['ir.config_parameter']
        ran_functions = IrConfig.get_param(
            'list_funct_generate_master_data_survey', '[]')
        ran_functions = safe_eval(ran_functions)
        if not isinstance(ran_functions, (list)):
            ran_functions = []
        if '_create_master_data_survey' in ran_functions:
            return True
        else:
            ran_functions.append('_create_master_data_survey')
            IrConfig.set_param(
                'list_funct_generate_master_data_survey', str(ran_functions))

        _logger.info("=== START: _create_master_data_survey ====")
        applied_jobs = [
            'supervisor',
            'skilled_tradesmen',
            'scaffolder',
            'sentries',
            'trades_assistant',
            'yards_person'
        ]
        basic_questions = [
            'full_name', 'preferred_name', 'email_address', 'contact_number',
            'position_applied_for', 'address', 'availability', 'references'
        ]
        positions = [
            'Scaffolder', 'Sentry', 'Yards person',
            'Dual trade Rigger Scaffolder',
            'Dual trade Carpenter Scaffolder',
            'Dual trade Electrician Scaffolder',
            'Dual trade boiler maker Scaffolder',
            'Dual trade Rope access technician Scaffolder (level 1)',
            'Dual trade Rope access technician Scaffolder (level 2)',
            'Dual trade Rope access technician Scaffolder (level 3)',
            'Trade Assistant', 'Scaffold Supervisor',
            'Health and Safety Advisor [HSE]', 'Trainer Assessor'
        ]

        SurveyPage = self.env['survey.page']
        SurveyQuestion = self.env['survey.question']
        SurveyLabel = self.env['survey.label']

        ResCountry = self.env['res.country']
        country_datas = ResCountry.search_read([], ["name"])
        country_names = list(set([c['name'] for c in country_datas]))

        in_progress = self.env.ref('survey.stage_in_progress', False)
        in_progress_id = in_progress and in_progress.id or False

        url_eoi = str(uuid.uuid4())
        tpl_sign_eoi = self.env.ref(
            'sms_recruitment_enhancement.template_sign_eoi', False)
        if tpl_sign_eoi and tpl_sign_eoi.share_link:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            url_eoi = "%s/sign/%s" % (base_url, tpl_sign_eoi.share_link)
        for job in applied_jobs:
            # Create survey
            survey = self.create({
                'title': 'Recruitment %s Form' % job.replace('_', ' ').title(),
                'stage_id': in_progress_id,
                'users_can_go_back': True
            })
            if survey:
                # Create survey page
                # Page 1: Basic Information
                page1 = SurveyPage.create({
                    'title': 'Basic Information',
                    'survey_id': survey.id,
                    'sequence': 5
                })
                if page1:
                    # Create 8 fix questions for 1st page "Basic Information"
                    seq_q1 = 5
                    for bq in basic_questions:
                        # 'full_name', 'preferred_name',
                        # 'email_address', 'contact_number'
                        # => type = 'textbox'
                        type = 'textbox'
                        if bq == 'position_applied_for':
                            type = 'simple_choice'
                        elif bq in ['address', 'availability', 'references']:
                            type = 'free_text'
                        vals1 = {
                            'page_id': page1.id,
                            'sequence': seq_q1,
                            'question': bq.replace('_', ' ').title(),
                            'type': type,
                            'constr_mandatory': True
                        }
                        if bq == 'email_address':
                            vals1.update({'validation_email': True})
                        if bq == 'position_applied_for':
                            vals1.update({'display_mode': 'dropdown'})
                        ques1 = SurveyQuestion.create(vals1)
                        seq_q1 += 5
                        # Create label for 'position_applied_for'
                        # Positions for the drop-down menu
                        if bq == 'position_applied_for':
                            seq_lbl1 = 5
                            for pos in positions:
                                SurveyLabel.create({
                                    'question_id': ques1.id,
                                    'sequence': seq_lbl1,
                                    'value': pos
                                })
                                seq_lbl1 += 5

                # Create page 2
                page2 = SurveyPage.create({
                    'title': 'Resume and EOI',
                    'survey_id': survey.id,
                    'sequence': 10
                })
                if page2:
                    # Create 2 fix questions for 2nd page "Resume and EOI"
                    SurveyQuestion.create({
                        'page_id': page2.id,
                        'sequence': 5,
                        'question': 'Resume',
                        'type': 'upload_file',
                        'constr_mandatory': True
                    })
                    SurveyQuestion.create({
                        'page_id': page2.id,
                        'sequence': 10,
                        'question': 'Expression of Interest',
                        'type': 'link',
                        'url_link': url_eoi
                    })
                # Create page 3
                page3 = SurveyPage.create({
                    'title': 'Certification',
                    'survey_id': survey.id,
                    'sequence': 15
                })
                if page3:
                    # Verification of Competency (VOC) Certificate
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 2,
                        'question':
                        'Verification of Competency (VOC) Certificate',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder'] else False,
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 4,
                        'question': 'Date Completed',
                        'type': 'date',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder'] else False,
                        'validation_required': True,
                        'is_period': True,
                        'period': 3,
                        'uot': 'months',
                        'date_type': 'issued',
                        'help_msg': 'Issued Date of Verification of '
                                    'Competency (VOC) Certificate',
                    })
                    # High Risk Work License (HRWL)
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 6,
                        'question': 'High Risk Work License (HRWL)',
                        'type': 'upload_file',
                        'constr_mandatory': True,
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 8,
                        'question': 'Licence Number',
                        'type': 'textbox',
                        'constr_mandatory': True,
                        'validation_length_min': 12,
                        'validation_length_max': 12,
                        'validation_error_msg':
                        'Licence Number should have 12 '
                        'alphanumeric chars',
                        'help_msg': 'High Risk Work License Number'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 10,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory': True,
                        'help_msg': 'Issued Date of High Risk Work License',
                    })
                    q_class = SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 12,
                        'question': 'Classes',
                        'type': 'multiple_choice',
                        'constr_mandatory': True,
                        'help_msg': 'Classes of High Risk Work License',
                    })
                    if q_class:
                        classes = ['DG', 'LF', 'RB', 'RI',
                                   'RA', 'SB', 'SI', 'SA', 'WP']
                        seq_cl = 5
                        for c in classes:
                            SurveyLabel.create({
                                'question_id': q_class.id,
                                'sequence': seq_cl,
                                'value': c
                            })
                    # Working at Heights (WAH)
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 14,
                        'question': 'Working at Heights (WAH)',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder'] else False,
                        'help_msg': 'Please ensure you have attached front '
                                    'and back copies of your Working at '
                                    'Heights certificate'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 16,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder'] else False,
                        'validation_required': True,
                        'is_period': True,
                        'period': 2,
                        'uot': 'years',
                        'date_type': 'issued',
                        'help_msg': 'Issued Date of Working at Heights (WAH)'
                    })
                    # Enter and Work in Confined Spaces (CSE)
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 18,
                        'question': 'Enter and Work in Confined Spaces (CSE)',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder', 'sentries'] else False,
                        'help_msg': 'Please ensure you have attached front '
                                    'and back copies of your Enter and Work '
                                    'in Confined Spaces certificate'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 20,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory':
                        True if job in ['supervisor', 'skilled_tradesmen',
                                        'scaffolder', 'sentries'] else False,
                        'validation_required': True,
                        'is_period': True,
                        'period': 2,
                        'uot': 'years',
                        'date_type': 'issued',
                        'help_msg': 'Issued Date of Enter and Work in '
                                    'Confined Spaces (CSE)'
                    })
                    # Construction Card
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 22,
                        'question': 'Construction Card',
                        'type': 'upload_file',
                        'constr_mandatory': True,
                        'help_msg': 'Please ensure you have attached front '
                                    'and rear copies of your Construction Card'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 24,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory': True,
                        'help_msg': 'Issued Date of Construction Card'
                    })
                    # Passport or Birth Certificate
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 26,
                        'question': 'Passport or Birth Certificate',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job != 'yards_person' else False,
                        'help_msg': "Please ensure you have attached a copy "
                                    "of the picture page of your passport."
                                    "\nIf you do not hold a passport, a copy "
                                    "of your Australian birth certificate."
                                    "\nIf uploading a birth certificate, "
                                    "this must be supported by a valid "
                                    "government issued ID, proof of age or "
                                    "drivers' licence"
                    })
                    q_country = SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 28,
                        'question': 'Country of issue',
                        'type': 'simple_choice',
                        'display_mode': 'dropdown',
                        'constr_mandatory':
                        True if job != 'yards_person' else False,
                        'help_msg': 'Passport or Birth Certificate'
                    })
                    # Create country label
                    if q_country:
                        seq_c = 1
                        for c_name in country_names:
                            SurveyLabel.create({
                                'question_id': q_country.id,
                                'sequence': seq_c,
                                'value': c_name
                            })
                            seq_c += 1
                    q_yn = SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 30,
                        'question':
                        'Do you have full working rights in Australia?',
                        'type': 'simple_choice',
                        'constr_mandatory':
                        True if job != 'yards_person' else False,
                        'help_msg': 'Passport or Birth Certificate'
                    })
                    # Create Yes/No Label
                    if q_yn:
                        seq_yn = 1
                        for y in ["Yes", "No"]:
                            SurveyLabel.create({
                                'question_id': q_yn.id,
                                'sequence': seq_yn,
                                'value': y
                            })
                            seq_yn += 1
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 32,
                        'question': 'Passport Number',
                        'type': 'textbox',
                        'constr_mandatory':
                        True if job != 'yards_person' else False,
                        'validation_required': True,
                        'validation_length_min': 10,
                        'validation_length_max': 10,
                        'validation_error_msg':
                        'Passport Number should have 10 alphanumeric chars',
                        'help_msg': 'Passport or Birth Certificate'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 34,
                        'question': 'Birth Certificate Number',
                        'type': 'textbox',
                        'constr_mandatory':
                        True if job != 'yards_person' else False,
                        'validation_required': True,
                        'validation_length_min': 15,
                        'validation_length_max': 15,
                        'validation_error_msg':
                        'Birth Certificate Number should have 15 '
                        'alphanumeric chars',
                        'help_msg': 'Passport or Birth Certificate'
                    })
                    # Section 44 Certificate
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 36,
                        'question': 'Section 44 Certificate',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job == 'supervisor' else False,
                        'help_msg': 'Please ensure you have attached a '
                                    'copy of your Section 44 certificate'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 38,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory':
                        True if job == 'supervisor' else False,
                        'help_msg': 'Issued Date of Section 44 Certificate'
                    })
                    # Official Trade Certificate / Qualification
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 40,
                        'question':
                        'Official Trade Certificate / Qualification',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job == 'skilled_tradesmen' else False,
                        'help_msg': 'Please ensure you have attached a copy '
                                    'of your Trade Certifications / '
                                    'Qualifications'
                    })
                    # Gas Test Certificate
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 42,
                        'question': 'Gas Test Certificate',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job == 'sentries' else False,
                        'help_msg': 'Please ensure you have attached front '
                                    'and back copies of your Gas Test '
                                    'Certificate'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 44,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory':
                        True if job == 'sentries' else False,
                        'help_msg': 'Issued Date of Gas Test Certificate'
                    })
                    # Fork Lift License
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 46,
                        'question': 'Fork Lift License',
                        'type': 'upload_file',
                        'constr_mandatory':
                        True if job in ['sentries', 'yards_person'] else False,
                        'help_msg': 'Please ensure you have attached front '
                                    'and back copies of your Fork Lift Licence'
                    })
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 48,
                        'question': 'Date Issued',
                        'type': 'date',
                        'constr_mandatory':
                        True if job in ['sentries', 'yards_person'] else False,
                        'help_msg': 'Issued Date of Fork Lift License'
                    })
                    # Drivers License
                    SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 50,
                        'question': 'Expiry Date',
                        'type': 'date',
                        'help_msg': 'Expiry Date of Drivers License'
                    })
                    q_driver_class = SurveyQuestion.create({
                        'page_id': page3.id,
                        'sequence': 52,
                        'question': 'Class of Licence',
                        'type': 'multiple_choice',
                        'help_msg': 'Class of Drivers Licence'
                    })
                    if q_driver_class:
                        seq_dr = 1
                    for d in ['C', 'LR', 'MR', 'HR', 'HC', 'MC']:
                        SurveyLabel.create({
                            'question_id': q_driver_class.id,
                            'sequence': seq_dr,
                            'value': d
                        })
                        seq_dr += 1
        _logger.info("=== END: _create_master_data_survey ====")
        return True

    @api.model
    def prepare_result(self, question, current_filters=None):
        result_summary = super(Survey, self).prepare_result(
            question, current_filters)
        if question.type == 'upload_file':
            result_summary = []
            for input_line in question.user_input_line_ids:
                if not(current_filters) or \
                        input_line.user_input_id.id in current_filters:
                    result_summary.append(input_line)
        return result_summary
