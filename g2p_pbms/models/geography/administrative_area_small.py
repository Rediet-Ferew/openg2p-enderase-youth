from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class G2PAdministrativeAreaSmall(models.Model):
    _name = "g2p.administrative.area.small"
    _description = "Administrative Area Small"
    _rec_name = "area_mnemonic"

    area_mnemonic = fields.Char(string="Area Mnemonic", required=True)
    area_description = fields.Char(string="Area Description", required=True)
    administrative_area_large_id = fields.Many2one(
        "g2p.administrative.area.large",
        string="Administrative Area Large",
        required=True,
    )
    administrative_area_large_mnemonic = fields.Char(
        string="Large Area Mnemonic",
        related="administrative_area_large_id.area_mnemonic",
        store=True,
        readonly=True,
    )
    administrative_area_large_description = fields.Char(
        string="Large Area Description",
        related="administrative_area_large_id.area_description",
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        (
            'unique_area_mnemonic',
            'unique(area_mnemonic)',
            'The Area Mnemonic must be unique!'
        )
    ]

    def action_open_edit(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "g2p.administrative.area.small",
            "view_mode": "form",
            "res_id": self.id,
        }
