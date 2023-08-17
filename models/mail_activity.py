# -*- coding: utf-8 -*- 

from odoo import models, fields, api, _,Command
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from random import randint

PROOF_CANCEL_ACTIVITY = 'proof_cancel_activity'
PROOF_CANCEL_ACTIVITY_DONE = 'proof_cancel_activity_done'

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    #FIXME: here we have added general field to prevent adding specific perpose field in general perpose object,
    context_note = fields.Char(string='Context note',help='This field help to detect the context of this activity')
    proof_cancel_state = fields.Selection([('planned','Planned'),
                                           ('done','Done')],compute='_compute_proof_cancel_state',
                                          string='Status')


    @api.depends('context_note')
    def _compute_proof_cancel_state(self):
        for each in self:
            each.proof_cancel_state = each.context_note == PROOF_CANCEL_ACTIVITY_DONE and 'done' or 'planned'

    @api.model_create_multi
    def create(self, vals_list):
        activities = super(MailActivity, self).create(vals_list)
        for activity in activities._filter_proof_cancel_activity():
            prepress_proof = self.env['prepress.proof'].browse(activity.res_id)
            prepress_proof.cancel_activities_planned += 1
        return activities


    def unlink(self):
        for activity in self._filter_proof_cancel_activity():
            if activity.context_note == PROOF_CANCEL_ACTIVITY_DONE:
                raise ValidationError(_("Can not remove Cancel Prepress proof done activity!"))
            prepress_proof = self.env['prepress.proof'].browse(activity.res_id)
            prepress_proof.cancel_activities_planned -= 1
        res = super(MailActivity,self).unlink()
        return res


    def _action_done(self, feedback=False, attachment_ids=None):
        """ Private implementation of marking activity as done: posting a message, deleting activity
            (since done), and eventually create the automatical next activity (depending on config).
            :param feedback: optional feedback from user when marking activity as done
            :param attachment_ids: list of ir.attachment ids to attach to the posted mail.message
            :returns (messages, activities) where
                - messages is a recordset of posted mail.message
                - activities is a recordset of mail.activity of forced automically created activities
        """
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []

        # Search for all attachments linked to the activities we are about to unlink. This way, we
        # can link them to the message posted and prevent their deletion.
        attachments = self.env['ir.attachment'].search_read([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ], ['id', 'res_id'])

        activity_attachments = defaultdict(list)
        for attachment in attachments:
            activity_id = attachment['res_id']
            activity_attachments[activity_id].append(attachment['id'])

        for activity in self:
            # extract value to generate next activities
            if activity.chaining_type == 'trigger':
                vals = activity.with_context(activity_previous_deadline=activity.date_deadline)._prepare_next_activity_values()
                next_activities_values.append(vals)

            # post message on activity, before deleting it
            record = self.env[activity.res_model].browse(activity.res_id)
            record.message_post_with_view(
                'mail.message_activity_done',
                values={
                    'activity': activity,
                    'feedback': feedback,
                    'display_assignee': activity.user_id != self.env.user
                },
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_activities'),
                mail_activity_type_id=activity.activity_type_id.id,
                attachment_ids=[Command.link(attachment_id) for attachment_id in attachment_ids] if attachment_ids else [],
            )

            # Moving the attachments in the message
            # TODO: Fix void res_id on attachment when you create an activity with an image
            # directly, see route /web_editor/attachment/add
            activity_message = record.message_ids[0]
            message_attachments = self.env['ir.attachment'].browse(activity_attachments[activity.id])
            if message_attachments:
                message_attachments.write({
                    'res_id': activity_message.id,
                    'res_model': activity_message._name,
                })
                activity_message.attachment_ids = message_attachments
            messages |= activity_message

        next_activities = self.env['mail.activity'].create(next_activities_values)
        if self.context_note == PROOF_CANCEL_ACTIVITY:
            self.context_note = PROOF_CANCEL_ACTIVITY_DONE
        else:
            self.unlink()  # will unlink activity, dont access `self` after that
        return messages, next_activities

    def activity_format(self):
        activities = self.filtered(lambda act:not act.context_note or not act.context_note.startswith('proof_cancel_activity_')).read()
        mail_template_ids = set([template_id for activity in activities for template_id in activity["mail_template_ids"]])
        mail_template_info = self.env["mail.template"].browse(mail_template_ids).read(['id', 'name'])
        mail_template_dict = dict([(mail_template['id'], mail_template) for mail_template in mail_template_info])
        for activity in activities:
            activity['mail_template_ids'] = [mail_template_dict[mail_template_id] for mail_template_id in activity['mail_template_ids']]
        return activities

    def _filter_proof_cancel_activity(self):
        return self.filtered(lambda act: act.context_note in (PROOF_CANCEL_ACTIVITY,PROOF_CANCEL_ACTIVITY_DONE) and act.res_model == 'prepress.proof')


