from odoo import api, fields, models

from odoo.addons.g2p_registry_type_addon.models import G2PRegistryType, G2PTargetModelMapping


class G2PRegistryDatabase(models.Model):
    _name = "g2p.registry.database"
    _description = "PBMS Registry Database"
    _rec_name = "name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    target_registry = fields.Selection(
        selection=G2PRegistryType.selection(),
        string="Target Registry Key",
        required=True,
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Odoo Domain Model",
        required=True,
        ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True)
    identifier_field = fields.Char(
        required=True,
        default="internal_record_id",
        help="Field selected by PBMS eligibility and entitlement SQL queries.",
    )
    base_domain = fields.Char(default="[]")

    _sql_constraints = [
        ("g2p_registry_database_code_unique", "unique(code)", "The registry database code must be unique."),
        (
            "g2p_registry_database_target_unique",
            "unique(target_registry)",
            "Each target registry key can only be configured once.",
        ),
    ]

    @api.onchange("target_registry")
    def _onchange_target_registry(self):
        for record in self:
            model_name = G2PTargetModelMapping.get_target_model_name(record.target_registry)
            if model_name:
                model = self.env["ir.model"].search([("model", "=", model_name)], limit=1)
                record.model_id = model
            record.identifier_field = G2PTargetModelMapping.get_target_identifier_field(
                record.target_registry
            )
