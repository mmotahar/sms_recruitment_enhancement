from odoo.tests.common import TransactionCase


class TestReportEditor(TransactionCase):

    def test_copy_inherit_report(self):
        report = self.env['ir.actions.report'].create({
            'name': 'test inherit report user',
            'report_name': 'web_studio.test_inherit_report_user',
            'model': 'res.users',
        })
        self.env['ir.ui.view'].create({
            'type': 'qweb',
            'name': 'web_studio.test_inherit_report_hi',
            'key': 'web_studio.test_inherit_report_hi',
            'arch': '''
                <t t-name="web_studio.test_inherit_report_hi">
                    hi
                </t>
            ''',
        })
        parent_view = self.env['ir.ui.view'].create({
            'type': 'qweb',
            'name': 'web_studio.test_inherit_report_user_parent',
            'key': 'web_studio.test_inherit_report_user_parent',
            'arch': '''
                <t t-name="web_studio.test_inherit_report_user_parent_view_parent">
                    <t t-call="web_studio.test_inherit_report_hi"/>!
                </t>
            ''',
        })
        self.env['ir.ui.view'].create({
            'type': 'qweb',
            'name': 'web_studio.test_inherit_report_user',
            'key': 'web_studio.test_inherit_report_user',
            'arch': '''
                <xpath expr="." position="inside">
                    <t t-call="web_studio.test_inherit_report_hi"/>!!
                </xpath>
            ''',
            'inherit_id': parent_view.id,

        })

        # check original report render to expected output
        report_html = report.render_template(report.report_name).decode('utf-8')
        self.assertEqual(''.join(report_html.split()), 'hi!hi!!')

        # duplicate original report
        report.copy_report_and_template()
        copy_report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'web_studio.test_inherit_report_user_copy_1'),
        ])

        # check duplicated report render to expected output
        copy_report_html = copy_report.render_template(copy_report.report_name).decode('utf-8')
        self.assertEqual(''.join(copy_report_html.split()), 'hi!hi!!')

        # check that duplicated view is inheritance combination of original view
        copy_view = self.env['ir.ui.view'].search([
            ('key', '=', copy_report.report_name),
        ])
        self.assertFalse(copy_view.inherit_id, 'copied view does not inherit another one')
        found = len(copy_view.arch_db.split('test_inherit_report_hi_copy_1')) - 1
        self.assertEqual(found, 2, 't-call is duplicated one time and used 2 times')
