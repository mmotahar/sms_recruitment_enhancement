##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2018 (<http://ioppolo.com.au>).
##############################################################################
from . import models
from . import controllers
from . import wizards
from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['survey.survey']._create_master_data_survey()
    env['sign.item']._create_sign_item_eoi()
    env['sign.item']._create_sign_item_payroll_info()
    env['sign.item']._create_sign_item_superannuation()
    env['sign.item']._create_sign_item_tax_declaration()
    env['sign.item']._create_sign_item_ppe_size_chart()
