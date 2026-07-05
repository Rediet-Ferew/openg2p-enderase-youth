from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class G2PAgency(models.Model):
    _name = "g2p.agency"
    _description = "Agency Model"
    _rec_name = "agency_mnemonic"

    name = fields.Char(string="Name", required=True)
    agency_mnemonic = fields.Char(string="Agency Mnemonic")

    admin_name = fields.Char(string="Admin Name")
    admin_email = fields.Char(string="Admin Email")
    admin_mobile = fields.Char(string="Admin Mobile")

    administrative_area_small_ids = fields.Many2many(
        "g2p.administrative.area.small",
        string="Administrative Areas (Small)"
    )
    agency_program_benefit_codes = fields.One2many(
        'g2p.agency.program.benefit.codes',
        'agency_id',
        string='Agency Program Benefit Codes'
    )

    _sql_constraints = [
        (
            'agency_mnemonic',
            'unique(agency_mnemonic)',
            'Agency Mnemonic must be unique!'
        )
    ]


    def action_open_edit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'g2p.agency',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context':{'create': False, 'agency_form_edit':True},
        }

