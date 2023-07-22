# -*- coding: utf-8 -*- 

from odoo import models, fields, api, _
from .mail_activity import PROOF_CANCEL_ACTIVITY
from odoo.exceptions import UserError, ValidationError
from random import randint


class PrepressProof(models.Model):
    _inherit = 'prepress.proof'

    state = fields.Selection(selection_add=[('pending_cancel', 'Pending cancel')],
                             ondelete={'pending_cancel': 'set default'})
    cancel_activities_count = fields.Integer(compute='_compute_cancel_activities_count')
    cancel_activities_planned = fields.Integer(string='Number of planned cancel activities')
    cancel_activities_done = fields.Integer(string='Number of done cancel activities',
                                            help='This is the number of all done activities including deleted/canceled ones')


    def action_cancel_with_motif(self):
        self._check_cancel_activities()
        return super(PrepressProof,self.with_context(default_cancel_motif_id=self.cancel_motif_id.id,
                                                     default_display_cancel_motif_id=False)).action_cancel_with_motif()
        #return super(PrepressProof, self.with_context(default_required_cancel_motif_id=False,
        #                                              default_display_cancel_motif_id=False)).action_cancel_with_motif()

    def _check_cancel_activities(self):
        for each in self:
            if not each.cancel_activities_planned:
                raise ValidationError(_("No planned activities has been detected,can not cancel Prepress proof [%s]")%each.name)
            if each.cancel_activities_planned != each.cancel_activities_done:
                raise ValidationError(_("All cancel activities must be done!"))


    def _compute_cancel_activities_count(self):
        for each in self:
            each.cancel_activities_count = len(each._get_cancel_activities())


    def _get_cancel_activities(self):
        self.ensure_one()
        cancel_activities_domain = self._get_cancel_activities_domain()
        return self.env['mail.activity'].search(cancel_activities_domain)

    def _get_cancel_activities_domain(self):
        return [('res_model', '=', 'prepress.proof'), ('res_id', '=', self.id),('context_note','=',PROOF_CANCEL_ACTIVITY)]

    def show_cancel_activities(self):
        self.ensure_one()
        return {
            'name': _('Cancel activities'),
            'view_mode': 'tree',
            'views': [(self.env.ref('prepress_proof_advanced_cancel.view_cancel_mail_activity_tree').id, 'tree')],
            'res_model': 'mail.activity',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {
                'default_res_model_id': self.env['ir.model'].search([('model', '=', 'prepress.proof')], limit=1).id,
                'default_res_id': self.id,
                'default_context_note':PROOF_CANCEL_ACTIVITY},
            'domain': [('id', 'in', self._get_cancel_activities().ids)]
        }

    def action_start_cancel_with_motif(self):
        return self.with_context(model=self._name,
                                 model_ids=self.ids,
                                 method='action_start_cancel',
                                 default_display_cancel_date=False)._action_cancel_motif_wizard()

    def action_start_cancel(self):
        # we have to remove the Cancel date because it will be filled by the standard wizard ,
        # in our case we have not achieve yet the cancelation
        self.write({'cancel_date': False})
        return self._action_start_cancel()

    def _action_start_cancel(self):
        self.write({'state': 'pending_cancel'})
