# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from .common import HelpdeskTransactionCase
from odoo import fields
from odoo.exceptions import AccessError


class TestHelpdeskFlow(HelpdeskTransactionCase):
    """ Test used to check that the base functionalities of Helpdesk function as expected.
        - test_access_rights: tests a few access rights constraints
        - test_assign_close_dates: tests the assignation and closing time get computed correctly
        - test_ticket_partners: tests the number of tickets of a partner is computed correctly
        - test_team_assignation_[method]: tests the team assignation method work as expected
    """

    def setUp(self):
        super(TestHelpdeskFlow, self).setUp()

    def test_access_rights(self):
        # helpdesk user should only be able to:
        #   read: teams, stages, SLAs, ticket types
        #   read, create, write, unlink: tickets, tags
        # helpdesk manager:
        #   read, create, write, unlink: everything (from helpdesk)
        # we consider in these tests that if the user can do it, the manager can do it as well (as the group is implied)
        def test_write_and_unlink(record):
            record.write({'name': 'test_write'})
            record.unlink()

        def test_not_write_and_unlink(self, record):
            with self.assertRaises(AccessError):
                record.write({'name': 'test_write'})
            with self.assertRaises(AccessError):
                record.unlink()
            # self.assertRaises(AccessError, record.write({'name': 'test_write'})) # , "Helpdesk user should not be able to write on %s" % record._name)
            # self.assertRaises(AccessError, record.unlink(), "Helpdesk user could unlink %s" % record._name)

        # helpdesk.team access rights
        team = self.env['helpdesk.team'].sudo(self.helpdesk_manager.id).create({'name': 'test'})
        team.sudo(self.helpdesk_user.id).read()
        test_not_write_and_unlink(self, team.sudo(self.helpdesk_user.id))
        with self.assertRaises(AccessError):
            team.sudo(self.helpdesk_user.id).create({'name': 'test create'})
        test_write_and_unlink(team)

        # helpdesk.ticket access rights
        ticket = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({'name': 'test'})
        ticket.read()
        test_write_and_unlink(ticket)

        # helpdesk.stage access rights
        stage = self.env['helpdesk.stage'].sudo(self.helpdesk_manager.id).create({
            'name': 'test',
            'team_ids': [(6, 0, [self.test_team.id])],
        })
        stage.sudo(self.helpdesk_user.id).read()
        test_not_write_and_unlink(self, stage.sudo(self.helpdesk_user.id))
        with self.assertRaises(AccessError):
            stage.sudo(self.helpdesk_user.id).create({
                'name': 'test create',
                'team_ids': [(6, 0, [self.test_team.id])],
            })
        test_write_and_unlink(stage)

        # helpdesk.sla access rights
        sla = self.env['helpdesk.sla'].sudo(self.helpdesk_manager.id).create({
            'name': 'test',
            'team_id': self.test_team.id,
            'stage_id': self.stage_done.id,
        })
        sla.sudo(self.helpdesk_user.id).read()
        test_not_write_and_unlink(self, sla.sudo(self.helpdesk_user.id))
        with self.assertRaises(AccessError):
            sla.sudo(self.helpdesk_user.id).create({
                'name': 'test create',
                'team_id': self.test_team.id,
                'stage_id': self.stage_done.id,
            })
        test_write_and_unlink(sla)

        # helpdesk.ticket.type access rights
        ticket_type = self.env['helpdesk.ticket.type'].sudo(self.helpdesk_manager.id).create({
            'name': 'test with unique name please',
        })
        ticket_type.sudo(self.helpdesk_user.id).read()
        test_not_write_and_unlink(self, ticket_type.sudo(self.helpdesk_user.id))
        with self.assertRaises(AccessError):
            ticket_type.sudo(self.helpdesk_user.id).create({
                'name': 'test create with unique name please',
            })
        test_write_and_unlink(ticket_type)

        # helpdesk.tag access rights
        tag = self.env['helpdesk.tag'].sudo(self.helpdesk_user.id).create({'name': 'test with unique name please'})
        tag.read()
        test_write_and_unlink(tag)

    def test_assign_close_dates(self):
        # helpdesk user create a ticket
        ticket1 = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'test ticket 1',
            'team_id': self.test_team.id,
        })
        # we rewind its creation date and set it to 2 days ago (we have to bypass the ORM as it doesn't let you write on create_date)
        ticket1._cr.execute(
            "UPDATE helpdesk_ticket set create_date=%s where id=%s",
            ["'" + fields.Datetime.to_string(fields.Datetime.from_string(fields.Datetime.now()) - relativedelta(days=2)) + "'", ticket1.id])
        # invalidate the cache and manually run the compute as our cr.execute() bypassed the ORM
        ticket1.invalidate_cache()
        # the helpdesk user takes the ticket
        ticket1.assign_ticket_to_self()
        # we verify the ticket is correctly assigned
        self.assertTrue(ticket1.user_id.id == ticket1._uid, "Assignation for ticket not correct")
        self.assertTrue(ticket1.assign_hours == 48, "Assignation time for ticket not correct")
        # we close the ticket and verify its closing time
        ticket1.write({'stage_id': self.stage_done.id})
        self.assertTrue(ticket1.close_hours == 48, "Close time for ticket not correct")

    def test_ticket_partners(self):
        # we create a partner
        partner = self.env['res.partner'].create({
            'name': 'Freddy Krueger'
        })
        # helpdesk user creates 2 tickets for the partner
        ticket1 = self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'partner ticket 1',
            'team_id': self.test_team.id,
            'partner_id': partner.id,
        })
        self.env['helpdesk.ticket'].sudo(self.helpdesk_user.id).create({
            'name': 'partner ticket 2',
            'team_id': self.test_team.id,
            'partner_id': partner.id,
        })
        self.assertTrue(ticket1.partner_tickets == 2, "Incorrect number of tickets from the same partner.")

    def test_team_assignation_randomly(self):
        # we put the helpdesk user and manager in the test_team's members
        self.test_team.member_ids = [(6, 0, [self.helpdesk_user.id, self.helpdesk_manager.id])]
        # we set the assignation method to randomly (=uniformly distributed)
        self.test_team.assign_method = 'randomly'
        # we create a bunch of tickets
        for i in range(10):
            self.env['helpdesk.ticket'].create({
                'name': 'test ticket ' + str(i),
                'team_id': self.test_team.id,
            })
        # ensure both members have the same amount of tickets assigned
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_user.id)]), 5)
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_manager.id)]), 5)

    def test_team_assignation_balanced(self):
        # we put the helpdesk user and manager in the test_team's members
        self.test_team.member_ids = [(6, 0, [self.helpdesk_user.id, self.helpdesk_manager.id])]
        # we set the assignation method to randomly (=uniformly distributed)
        self.test_team.assign_method = 'balanced'
        # we create a bunch of tickets
        for i in range(4):
            self.env['helpdesk.ticket'].create({
                'name': 'test ticket ' + str(i),
                'team_id': self.test_team.id,
            })
        # ensure both members have the same amount of tickets assigned
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_user.id)]), 2)
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_manager.id)]), 2)

        # helpdesk user finishes his 2 tickets
        self.env['helpdesk.ticket'].search([('user_id', '=', self.helpdesk_user.id)]).write({'stage_id': self.stage_done.id})

        # we create 4 new tickets
        for i in range(4):
            self.env['helpdesk.ticket'].create({
                'name': 'test ticket ' + str(i),
                'team_id': self.test_team.id,
            })

        # ensure both members have the same amount of tickets assigned
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_user.id), ('close_date', '=', False)]), 3)
        self.assertEqual(self.env['helpdesk.ticket'].search_count([('user_id', '=', self.helpdesk_manager.id), ('close_date', '=', False)]), 3)
