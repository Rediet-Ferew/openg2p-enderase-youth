from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class G2PWarehouse(models.Model):
    _name = "g2p.warehouse"
    _description = "Warehouse Model"
    _rec_name = "warehouse_mnemonic"

    name = fields.Char(string="Warehouse Name", required=True)
    warehouse_mnemonic = fields.Char(string="Warehouse Mnemonic")
    is_sponsor_bank = fields.Boolean(
        string="Is Sponsor Bank",
        help="Does this service provider operate as a sponsor bank?",
        default=False
    )
    admin_name = fields.Char(string="Admin Name")
    admin_email = fields.Char(string="Admin Email")
    admin_mobile = fields.Char(string="Admin Mobile")
    administrative_area_large_ids = fields.Many2many(
        "g2p.administrative.area.large",
        string="Administrative Areas (Large)"
    )
    warehouse_program_benefit_codes = fields.One2many(
        "g2p.warehouse.program.benefit.codes",
        "warehouse_id",
        string="Warehouse Program Benefit Codes"
    )

    _sql_constraints = [
        (
            'warehouse_mnemonic',
            'unique(warehouse_mnemonic)',
            'Warehouse Mnemonic must be unique!'
        )
    ]

    def action_open_edit(self):
        self.ensure_one()
        xmlid = "g2p_pbms.view_g2p_sponsor_bank_form" if self.is_sponsor_bank else "g2p_pbms.view_g2p_warehouse_form"
        view_id = self.env.ref(xmlid).id
        return {
            "type": "ir.actions.act_window",
            "res_model": "g2p.warehouse",
            "res_id": self.id,
            "view_mode": "form",
            "views": [(view_id, "form")],
            "target": "current",
            "context": {"create": False, "warehouse_form_edit": True},
        }

    def action_open_create_warehouse(self):
        view_id = self.env.ref("g2p_pbms.view_g2p_warehouse_form").id
        return {
            "type": "ir.actions.act_window",
            "name": "Warehouse",
            "res_model": "g2p.warehouse",
            "view_mode": "form",
            "views": [(view_id, "form")],
            "target": "current",
            "context": {"create": True, "default_is_sponsor_bank": False, "warehouse_form_edit": True},
        }

    def action_open_create_sponsor_bank(self):
        view_id = self.env.ref("g2p_pbms.view_g2p_sponsor_bank_form").id
        return {
            "type": "ir.actions.act_window",
            "name": "Sponsor Bank",
            "res_model": "g2p.warehouse",
            "view_mode": "form",
            "views": [(view_id, "form")],
            "target": "current",
            "context": {"create": True, "default_is_sponsor_bank": True, "warehouse_form_edit": True},
        }