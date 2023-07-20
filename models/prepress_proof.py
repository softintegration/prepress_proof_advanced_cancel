# -*- coding: utf-8 -*- 

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from random import randint


class PrepressProof(models.Model):
    _inherit = 'prepress.proof'

    state = fields.Selection(selection_add=[('pending_cancel', 'Pending cancel')],ondelete={'pending_cancel': 'set default'})


    def action_start_cancel_with_motif(self):
        return self.with_context(model=self._name,
                                 model_ids=self.ids,
                                 method='action_start_cancel',
                                 default_display_cancel_date=False)._action_cancel_motif_wizard()

    def action_start_cancel(self):
        # we have to remove the Cancel date because it will be filled by the standard wizard ,
        # in our case we have not achieve yet the cancelation
        self.write({'cancel_date':False})
        return self._action_start_cancel()

    def _action_start_cancel(self):
        self.write({'state': 'pending_cancel'})

