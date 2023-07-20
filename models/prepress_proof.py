# -*- coding: utf-8 -*- 

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from random import randint


class PrepressProof(models.Model):
    _inherit = 'prepress.proof'

    state = fields.Selection(selection_add=[('pending_cancel', 'Pending cancel')],ondelete={'pending_cancel': 'set default'})


    def action_start_cancel(self):
        return self._action_start_cancel()

    def _action_start_cancel(self):
        self.write({'state': 'pending_cancel'})

