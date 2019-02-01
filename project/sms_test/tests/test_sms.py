# -*- coding: utf-8 -*-

from openerp.addons.test_runner.lib import case  # @UnresolvedImport


class TestDummy(case.ModuleCase):

    load = [
        # load some data for your test, in csv, xml or yaml format
        # ex: 'data/res.users.csv'
    ]

    def test_something(self):
        """
        Explain your test here
        """

        # do your test here !
        self.assertEquals(True, True)
