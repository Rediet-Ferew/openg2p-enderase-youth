# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class EnderaseLookupMixin(models.AbstractModel):
    _name = "g2p.enderase.lookup.mixin"
    _description = "Enderase Lookup Mixin"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if record.code and record.code != record.code.strip():
                raise ValidationError(_("Code must not contain leading or trailing spaces."))


class EnderaseAdminRegion(models.Model):
    _name = "g2p.enderase.admin.region"
    _description = "Enderase Administrative Region"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_admin_region_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseAdminZone(models.Model):
    _name = "g2p.enderase.admin.zone"
    _description = "Enderase Administrative Zone"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_admin_zone_code_unique", "unique(code)", "The code must be unique."),
    ]

    region_id = fields.Many2one("g2p.enderase.admin.region", required=True, index=True)


class EnderaseAdminWoreda(models.Model):
    _name = "g2p.enderase.admin.woreda"
    _description = "Enderase Administrative Woreda"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_admin_woreda_code_unique", "unique(code)", "The code must be unique."),
    ]

    region_id = fields.Many2one("g2p.enderase.admin.region", required=True, index=True)
    zone_id = fields.Many2one("g2p.enderase.admin.zone", required=True, index=True)


class EnderaseSubcity(models.Model):
    _name = "g2p.enderase.subcity"
    _description = "Enderase Subcity"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_subcity_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseProfession(models.Model):
    _name = "g2p.enderase.profession"
    _description = "Enderase Profession"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_profession_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseEducationLevel(models.Model):
    _name = "g2p.enderase.education.level"
    _description = "Enderase Education Level"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "id"
    _sql_constraints = [
        ("enderase_education_level_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseEmploymentStatus(models.Model):
    _name = "g2p.enderase.employment.status"
    _description = "Enderase Employment Status"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "id"
    _sql_constraints = [
        ("enderase_employment_status_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseTrainingArea(models.Model):
    _name = "g2p.enderase.training.area"
    _description = "Enderase Training Area"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_training_area_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseTrainingSchedule(models.Model):
    _name = "g2p.enderase.training.schedule"
    _description = "Enderase Training Schedule"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "id"
    _sql_constraints = [
        ("enderase_training_schedule_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseSupportService(models.Model):
    _name = "g2p.enderase.support.service"
    _description = "Enderase Support Service"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_support_service_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseInterestArea(models.Model):
    _name = "g2p.enderase.interest.area"
    _description = "Enderase Interest Area"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "name"
    _sql_constraints = [
        ("enderase_interest_area_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseHearAbout(models.Model):
    _name = "g2p.enderase.hear.about"
    _description = "Enderase Hear About Source"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "id"
    _sql_constraints = [
        ("enderase_hear_about_code_unique", "unique(code)", "The code must be unique."),
    ]


class EnderaseMembershipType(models.Model):
    _name = "g2p.enderase.membership.type"
    _description = "Enderase Membership Type"
    _inherit = "g2p.enderase.lookup.mixin"
    _order = "id"
    _sql_constraints = [
        ("enderase_membership_type_code_unique", "unique(code)", "The code must be unique."),
    ]
