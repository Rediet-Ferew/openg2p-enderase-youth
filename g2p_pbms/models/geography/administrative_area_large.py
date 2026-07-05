from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class G2PAdministrativeAreaLarge(models.Model):
    _name = "g2p.administrative.area.large"
    _description = "Administrative Area Large"
    _rec_name = "area_mnemonic"

    area_mnemonic = fields.Char(string="Area Mnemonic", required=True)
    area_description = fields.Char(string="Area Description", required=True)

    _sql_constraints = [
        (
            'unique_area_mnemonic',
            'unique(area_mnemonic)',
            'The Area Mnemonic must be unique!'
        )
    ]

    def action_open_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "View Administrative Area (Large) Details",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "flags": {"mode": "readonly"},
        }

    def action_open_edit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'g2p.administrative.area.large',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False, 'area_form_edit': True},
        }