# -*- coding: utf-8 -*- 

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from random import randint

PROOF_CANCEL_ACTIVITY = 'proof_cancel_activity'

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    #FIXME: here we have added general field to prevent adding specific perpose field in general perpose object,
    context_note = fields.Char(string='Context note',help='This field help to detect the context of this activity')

    @api.model_create_multi
    def create(self, vals_list):
        activities = super(MailActivity, self).create(vals_list)
        for activity in activities._filter_proof_cancel_activity():
            prepress_proof = self.env['prepress.proof'].browse(activity.res_id)
            prepress_proof.cancel_activities_planned += 1
        return activities


    def unlink(self):
        for activity in self._filter_proof_cancel_activity():
            prepress_proof = self.env['prepress.proof'].browse(activity.res_id)
            prepress_proof.cancel_activities_done += 1
        res = super(MailActivity,self).unlink()
        return res


    def _filter_proof_cancel_activity(self):
        return self.filtered(lambda act: act.context_note == PROOF_CANCEL_ACTIVITY and act.res_model == 'prepress.proof')