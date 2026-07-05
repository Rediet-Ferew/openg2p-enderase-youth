import json
import logging

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from odoo.addons.g2p_registry_type_addon.models import G2PRegistryType, G2PTargetModelMapping

_logger = logging.getLogger(__name__)


NUMERIC_FIELD_TYPES = {
    "integer",
    "float",
    "double",
    "monetary",
    "numeric",
    "biginteger",
    "smallinteger",
    "decimal",
}


def _registry_database_for_rule(record):
    if record.program_id and record.program_id.registry_database_id:
        return record.program_id.registry_database_id
    return record.env["g2p.registry.database"].search(
        [("target_registry", "=", record.target_registry)],
        limit=1,
    )


def _target_for_vals(env, vals):
    program = env["g2p.program.definition"].browse(vals.get("program_id")) if vals.get("program_id") else None
    if program and program.registry_database_id:
        vals = dict(vals)
        vals["target_registry"] = program.registry_database_id.target_registry
    return vals


def _compute_rule_sql(record):
    try:
        domain_value = safe_eval(record.pbms_domain or "[]")
    except Exception as exc:
        _logger.error("Error evaluating PBMS domain for rule %s: %s", record.display_name, exc)
        return "Invalid domain"

    registry_db = _registry_database_for_rule(record)
    target_model_name = (
        registry_db.model_name
        or G2PTargetModelMapping.get_target_model_name(record.target_registry)
    )
    if not target_model_name:
        _logger.error("Unknown target registry '%s' for rule %s", record.target_registry, record.display_name)
        return "Unknown target registry type"

    target_model = record.env[target_model_name]
    identifier_field = (
        registry_db.identifier_field
        or G2PTargetModelMapping.get_target_identifier_field(record.target_registry)
    )
    if identifier_field not in target_model._fields:
        _logger.error(
            "Unknown identifier field '%s' on model '%s' for rule %s",
            identifier_field,
            target_model_name,
            record.display_name,
        )
        return "Unknown registry identifier field"

    try:
        query = target_model._where_calc(domain_value)
        from_clause, where_clause, where_clause_params = query.get_sql()
    except Exception as exc:
        _logger.error("Error generating SQL for rule %s: %s", record.display_name, exc)
        return "Error generating SQL"

    where_str = (" WHERE %s" % where_clause) if where_clause else ""
    query_str = (
        'SELECT "%s"."%s" FROM ' % (target_model._table, identifier_field)
    ) + from_clause + where_str
    formatted_params = ["'" + str(param) + "'" for param in where_clause_params]
    try:
        return query_str % tuple(formatted_params)
    except Exception as exc:
        _logger.error("Error formatting SQL for rule %s: %s", record.display_name, exc)
        return "Error formatting query"


class G2PEligibilityRuleDefinition(models.Model):
    _inherit = "g2p.eligibility.rule.definition"

    target_registry = fields.Selection(selection=G2PRegistryType.selection(), string="Target Registry", required=True)
    registry_database_id = fields.Many2one(
        "g2p.registry.database",
        related="program_id.registry_database_id",
        string="Registry Database",
        readonly=True,
        store=False,
    )
    registry_model_name = fields.Char(related="program_id.registry_model_name", readonly=True, store=False)

    @api.onchange("program_id")
    def _onchange_program_id_registry(self):
        for record in self:
            if record.program_id and record.program_id.registry_database_id:
                record.target_registry = record.program_id.registry_database_id.target_registry

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([_target_for_vals(self.env, vals) for vals in vals_list])

    def write(self, vals):
        vals = _target_for_vals(self.env, vals) if vals.get("program_id") else vals
        return super().write(vals)

    @api.depends("pbms_domain", "target_registry", "program_id.registry_database_id")
    def _get_query(self):
        for record in self:
            record.sql_query = _compute_rule_sql(record)


class G2PEntitlementRuleDefinition(models.Model):
    _inherit = "g2p.entitlement.rule.definition"

    target_registry = fields.Selection(selection=G2PRegistryType.selection(), string="Target Registry", required=True)
    registry_database_id = fields.Many2one(
        "g2p.registry.database",
        related="program_id.registry_database_id",
        string="Registry Database",
        readonly=True,
        store=False,
    )
    registry_model_name = fields.Char(related="program_id.registry_model_name", readonly=True, store=False)

    @api.onchange("program_id")
    def _onchange_program_id_registry(self):
        for record in self:
            if record.program_id and record.program_id.registry_database_id:
                record.target_registry = record.program_id.registry_database_id.target_registry

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([_target_for_vals(self.env, vals) for vals in vals_list])

    def write(self, vals):
        vals = _target_for_vals(self.env, vals) if vals.get("program_id") else vals
        return super().write(vals)

    @api.depends("target_registry", "program_id.registry_database_id")
    def _compute_multiplier_options(self):
        for record in self:
            model_name = (
                record.registry_model_name
                or G2PTargetModelMapping.get_target_model_name(record.target_registry)
            )
            if not model_name:
                record.allowed_multipliers = "[]"
                continue
            model = self.env[model_name]
            numeric_fields = [
                (name, field.string or name)
                for name, field in model._fields.items()
                if field.type in NUMERIC_FIELD_TYPES and name != "id"
            ]
            record.allowed_multipliers = json.dumps(numeric_fields)

    @api.depends("pbms_domain", "target_registry", "program_id.registry_database_id")
    def _get_query(self):
        for record in self:
            record.sql_query = _compute_rule_sql(record)
