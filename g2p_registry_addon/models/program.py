from odoo import api, fields, models


class G2PProgramDefinition(models.Model):
    _inherit = "g2p.program.definition"

    registry_database_id = fields.Many2one(
        "g2p.registry.database",
        string="Registry Database",
        required=True,
        ondelete="restrict",
        default=lambda self: self._default_registry_database_id(),
    )
    registry_model_name = fields.Char(
        related="registry_database_id.model_name",
        string="Registry Model",
        store=True,
        readonly=True,
    )
    registry_identifier_field = fields.Char(
        related="registry_database_id.identifier_field",
        string="Registry Identifier Field",
        store=True,
        readonly=True,
    )

    def _default_registry_database_id(self):
        registry_db = self.env.ref(
            "g2p_registry_addon.registry_database_enderase_youth",
            raise_if_not_found=False,
        )
        if registry_db:
            return registry_db.id
        return self.env["g2p.registry.database"].search([("active", "=", True)], limit=1).id

    def _registry_database_for_vals(self, vals):
        registry_db = self.env["g2p.registry.database"]
        if vals.get("registry_database_id"):
            return registry_db.browse(vals["registry_database_id"])
        if vals.get("target_registry"):
            return registry_db.search([("target_registry", "=", vals["target_registry"])], limit=1)
        default_id = self._default_registry_database_id()
        return registry_db.browse(default_id) if default_id else registry_db

    def _with_registry_target(self, vals):
        vals = dict(vals)
        registry_db = self._registry_database_for_vals(vals)
        if registry_db:
            vals.setdefault("registry_database_id", registry_db.id)
            vals["target_registry"] = registry_db.target_registry
        return vals

    @api.onchange("registry_database_id")
    def _onchange_registry_database_id(self):
        for record in self:
            if record.registry_database_id:
                record.target_registry = record.registry_database_id.target_registry

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._with_registry_target(vals) for vals in vals_list])

    def write(self, vals):
        if "registry_database_id" in vals and "target_registry" not in vals:
            registry_db = self.env["g2p.registry.database"].browse(vals["registry_database_id"])
            vals = dict(vals, target_registry=registry_db.target_registry)
        return super().write(vals)
