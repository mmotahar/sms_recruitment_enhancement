##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2018 (<http://ioppolo.com.au>).
##############################################################################
{
    "name": "SMS Recruitment Enhancement",
    "version": "1.0",
    "category": "Trobz Standard Modules",
    "description": """
This module aims to enhance the features of online recruitment
    """,
    "website": "http://ioppolo.com.au",
    "author": "Ioppolo & Associates",
    "category": "Ioppolo & Associates",
    "depends": [
        "hr_recruitment_survey",
        "sign",
    ],
    "data": [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        # "security/",

        # ============================================================
        # DATA
        # ============================================================
        # "data/",

        # ============================================================
        # VIEWS
        # ============================================================
        # "views/",
        'views/survey_question_template.xml',
        'views/survey_user_input_line_view.xml',
        'views/survey_question_view.xml',
        # ============================================================
        # MENU
        # ============================================================
        # "menu/",

        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        # "data/sms_update_functions_data.xml",
    ],

    "test": [],
    "demo": [],

    "installable": True,
    "active": False,
    "application": False,
}
