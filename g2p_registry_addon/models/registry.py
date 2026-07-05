from odoo import fields, models


class G2PRegistry(models.AbstractModel):
    _name = "g2p.registry"
    _description = "Abstract G2P Registry"

    link_registry_id = fields.Char(string="Link Registry ID", index=True)
    internal_record_id = fields.Char(string="Internal Record ID", index=True)
    registration_date = fields.Date(string="Registration Date")
    priority_rank = fields.Integer(string="Priority Rank")

    def action_open_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "View Registry Record",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "flags": {"mode": "readonly"},
        }

