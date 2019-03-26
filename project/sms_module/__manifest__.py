{
    'name': 'Project SMS installer',
    'version': '1.0',
    'category': 'Trobz Standard Modules',
    'description': """
This module will install all module dependencies of SMS.
    """,
    'author': 'Trobz',
    'website': 'http://www.trobz.com',
    'depends': [
        'hr_recruitment_survey',
        'sign'
    ],
    'data': [
        # ============================================================
        # SECURITY SETTING - GROUP - PROFILE
        # ============================================================
        # 'security/',

        # ============================================================
        # DATA
        # ============================================================
        # 'data/',

        # ============================================================
        # VIEWS
        # ============================================================
        # 'view/',

        # ============================================================
        # MENU
        # ============================================================
        # 'menu/',

        # ============================================================
        # FUNCTION USED TO UPDATE DATA LIKE POST OBJECT
        # ============================================================
        # "data/lighting_update_functions_data.xml",
    ],

    'test': [],
    'demo': [],

    'installable': True,
    'active': False,
    'application': False,
}
