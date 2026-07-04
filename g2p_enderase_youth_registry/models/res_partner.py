# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    enderase_registry_id = fields.Char(
        string="Enderase Registry ID",
        compute="_compute_enderase_registry_id",
        store=True,
        index=True,
        copy=False,
    )
    is_enderase_member = fields.Boolean(string="Enderase Member", index=True)
    is_enderase_beneficiary = fields.Boolean(string="Enderase Beneficiary", index=True)
    is_enderase_group = fields.Boolean(string="Enderase Group", index=True)
    is_enderase_startup = fields.Boolean(string="Enderase Startup", index=True)
    enderase_record_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("verified", "Verified"),
            ("active", "Active"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        default="draft",
        index=True,
        tracking=True,
    )
    enderase_membership_status = fields.Selection(
        [
            ("not_member", "Not Member"),
            ("applied", "Applied"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("rejected", "Rejected"),
        ],
        default="not_member",
        index=True,
    )
    enderase_beneficiary_category = fields.Selection(
        [("individual", "Individual"), ("group", "Group")],
        compute="_compute_enderase_beneficiary_category",
        store=True,
        readonly=False,
        index=True,
    )
    enderase_beneficiary_type = fields.Selection(
        [
            ("member", "Member"),
            ("group", "Group"),
            ("startup", "Startup"),
            ("service_recipient", "Service Recipient"),
            ("representative", "Representative"),
        ],
        index=True,
    )

    # ODK/source profile fields.
    enderase_full_name = fields.Char(string="Full Name")
    fayda_national_id = fields.Char(string="Fayda/National ID", index=True)
    date_of_birth = fields.Date(related="birthdate", readonly=False, store=True, string="Date of Birth")
    enderase_nationality = fields.Char(string="Nationality")
    enderase_admin_region_id = fields.Many2one("g2p.enderase.admin.region", string="Region")
    enderase_admin_zone_id = fields.Many2one(
        "g2p.enderase.admin.zone",
        string="Zone",
        domain="[('region_id', '=', enderase_admin_region_id)]",
    )
    enderase_admin_woreda_id = fields.Many2one(
        "g2p.enderase.admin.woreda",
        string="Woreda",
        domain="[('zone_id', '=', enderase_admin_zone_id)]",
    )
    enderase_kebele_name = fields.Char(string="Kebele Name")
    enderase_subcity_id = fields.Many2one("g2p.enderase.subcity", string="Subcity")

    occupation_profession_id = fields.Many2one("g2p.enderase.profession", string="Occupation/Profession")
    profession_other = fields.Char(string="Other Occupation/Profession")
    educational_level_id = fields.Many2one("g2p.enderase.education.level", string="Educational Level")
    employment_status_id = fields.Many2one("g2p.enderase.employment.status", string="Employment Status")

    current_skills = fields.Text(string="Current Skills")
    previous_training_received = fields.Text(string="Previous Training Received")
    certifications_held = fields.Text(string="Certifications Held")
    desired_training_area_ids = fields.Many2many(
        "g2p.enderase.training.area",
        "g2p_enderase_partner_training_area_rel",
        "partner_id",
        "training_area_id",
        string="Desired Training Areas",
    )
    training_area_other = fields.Char(string="Other Desired Training Area")
    preferred_training_schedule_ids = fields.Many2many(
        "g2p.enderase.training.schedule",
        "g2p_enderase_partner_training_schedule_rel",
        "partner_id",
        "training_schedule_id",
        string="Preferred Training Schedule",
    )
    interested_starting_business = fields.Selection([("yes", "Yes"), ("no", "No")])
    business_area_interest = fields.Char(string="Business Area of Interest")
    required_support_ids = fields.Many2many(
        "g2p.enderase.support.service",
        "g2p_enderase_partner_support_service_rel",
        "partner_id",
        "support_service_id",
        string="Required Support",
    )

    previous_membership = fields.Char(string="Previous Membership")
    experience_skill_area = fields.Text(string="Experience or Skill Area")
    reason_for_joining = fields.Text(string="Reason for Joining")
    interest_area_ids = fields.Many2many(
        "g2p.enderase.interest.area",
        "g2p_enderase_partner_interest_area_rel",
        "partner_id",
        "interest_area_id",
        string="Interest Areas",
    )
    interest_area_other = fields.Char(string="Other Interest Area")
    why_join = fields.Text(string="Why Join")
    career_path = fields.Text(string="Career or Life Path")
    skills_to_develop = fields.Text(string="Skills or Talents to Develop")
    challenges_faced = fields.Text(string="Challenges Faced")
    support_ambitions = fields.Text(string="Support for Ambitions")
    leadership_growth = fields.Text(string="Leadership Growth")
    view_of_enderase = fields.Text(string="View of Enderase")
    value_to_members_community = fields.Text(string="Value to Members and Community")
    hear_about_id = fields.Many2one("g2p.enderase.hear.about", string="How Did You Hear About Enderase?")
    hear_about_other = fields.Char(string="Other Source")
    membership_type_id = fields.Many2one("g2p.enderase.membership.type", string="Membership Type")
    declaration = fields.Selection([("agree", "Agree"), ("disagree", "Disagree")])

    # Group/startup profile fields.
    startup_name = fields.Char(string="Group/Startup Name", index=True)
    organization_name = fields.Char()
    organization_type = fields.Selection(
        [
            ("private", "Private"),
            ("non_profit", "Non-profit Organization"),
            ("public", "Public"),
            ("other", "Other"),
        ],
    )
    group_type = fields.Selection(
        [
            ("startup", "Startup"),
            ("collective", "Collective"),
            ("community", "Community"),
            ("association", "Association"),
            ("organization", "Organization"),
            ("other", "Other"),
        ],
        string="Group Type",
    )
    representative_role = fields.Char()
    primary_sector = fields.Char()
    support_category = fields.Char()
    support_needed = fields.Text()
    profile_description = fields.Text()
    participation_expectation = fields.Text()
    business_registration_status = fields.Text()
    selected_for_showcase = fields.Selection([("yes", "Yes"), ("no", "No")])
    interested_in_collaboration = fields.Selection([("yes", "Yes"), ("no", "No")])
    collaboration_interest = fields.Text()
    hiring_or_recruiting = fields.Selection([("yes", "Yes"), ("no", "No")])
    hiring_notes = fields.Text()
    needs_follow_up = fields.Boolean()

    source_reference = fields.Char(index=True)
    rec_import_source_label = fields.Char(string="Import Source")
    odk_instance_id = fields.Char(string="ODK Instance ID", index=True, copy=False)
    raw_source_payload = fields.Text(string="Raw Source Payload", copy=False)

    _sql_constraints = [
        ("enderase_registry_id_unique", "unique(enderase_registry_id)", "Enderase Registry ID must be unique."),
    ]

    def _is_enderase_registry_record(self):
        self.ensure_one()
        return (
            self.is_enderase_member
            or self.is_enderase_beneficiary
            or self.is_enderase_group
            or self.is_enderase_startup
        )

    @api.depends(
        "unique_id",
        "is_group",
        "is_registrant",
        "is_enderase_member",
        "is_enderase_beneficiary",
        "is_enderase_group",
        "is_enderase_startup",
    )
    def _compute_enderase_registry_id(self):
        for record in self:
            if record.unique_id and (
                record.is_enderase_member
                or record.is_enderase_beneficiary
                or record.is_enderase_group
                or record.is_enderase_startup
            ):
                prefix = "EY-G" if record.is_group else "EY-I"
                record.enderase_registry_id = f"{prefix}-{record.unique_id}"
            else:
                record.enderase_registry_id = False

    @api.depends("is_group")
    def _compute_enderase_beneficiary_category(self):
        for record in self:
            record.enderase_beneficiary_category = "group" if record.is_group else "individual"

    @api.onchange("enderase_full_name", "is_group")
    def _onchange_enderase_full_name(self):
        if not self.is_group and self.enderase_full_name:
            self.name = self.enderase_full_name

    @api.onchange("startup_name", "is_group")
    def _onchange_startup_name(self):
        if self.is_group and self.startup_name:
            self.name = self.startup_name

    @api.onchange("group_type", "is_enderase_group", "is_enderase_startup")
    def _onchange_enderase_group_type(self):
        if self.is_group and (self.is_enderase_group or self.is_enderase_startup or self.group_type):
            self.is_enderase_group = True
            self.is_enderase_beneficiary = True
        if self.is_group and self.group_type == "startup":
            self.is_enderase_startup = True
            self.enderase_beneficiary_type = "startup"
        elif self.is_group and self.is_enderase_startup and not self.group_type:
            self.group_type = "startup"
            self.enderase_beneficiary_type = "startup"
        elif self.is_group and self.is_enderase_group and not self.enderase_beneficiary_type:
            self.enderase_beneficiary_type = "group"

    @api.onchange("enderase_admin_region_id")
    def _onchange_enderase_admin_region_id(self):
        if self.enderase_admin_zone_id.region_id != self.enderase_admin_region_id:
            self.enderase_admin_zone_id = False
            self.enderase_admin_woreda_id = False

    @api.onchange("enderase_admin_zone_id")
    def _onchange_enderase_admin_zone_id(self):
        if self.enderase_admin_woreda_id.zone_id != self.enderase_admin_zone_id:
            self.enderase_admin_woreda_id = False

    @api.constrains("email")
    def _check_enderase_email(self):
        pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
        for record in self:
            if record._is_enderase_registry_record() and record.email and not pattern.match(record.email):
                raise ValidationError(_("Enter a valid email address."))

    @api.constrains("birthdate")
    def _check_enderase_birthdate(self):
        for record in self:
            if record._is_enderase_registry_record() and record.birthdate and record.birthdate > fields.Date.today():
                raise ValidationError(_("Date of birth cannot be in the future."))

    @api.constrains(
        "enderase_record_status",
        "declaration",
        "occupation_profession_id",
        "profession_other",
        "desired_training_area_ids",
        "training_area_other",
        "interest_area_ids",
        "interest_area_other",
        "hear_about_id",
        "hear_about_other",
        "interested_starting_business",
        "business_area_interest",
    )
    def _check_enderase_required_profile_fields(self):
        for record in self:
            if not record._is_enderase_registry_record():
                continue
            if record.is_enderase_member and record.enderase_record_status == "active" and record.declaration != "agree":
                raise ValidationError(_("Active Enderase members must agree to the declaration."))
            if record.occupation_profession_id.code == "other" and not record.profession_other:
                raise ValidationError(_("Other occupation/profession is required when occupation is Other."))
            if record.hear_about_id.code == "other" and not record.hear_about_other:
                raise ValidationError(_("Other source is required when hear-about source is Other."))
            if record.interested_starting_business == "yes" and not record.business_area_interest:
                raise ValidationError(_("Business area of interest is required when interested in starting a business."))
            if record._has_lookup_code(record.desired_training_area_ids, "other") and not record.training_area_other:
                raise ValidationError(_("Other desired training area is required when selected."))
            if record._has_lookup_code(record.interest_area_ids, "other") and not record.interest_area_other:
                raise ValidationError(_("Other interest area is required when selected."))

    def _has_lookup_code(self, records, code):
        return any(record.code == code for record in records)

    def action_enderase_submit(self):
        self.write({"enderase_record_status": "submitted"})

    def action_enderase_verify(self):
        self.write({"enderase_record_status": "verified"})

    def action_enderase_activate(self):
        self.write({"enderase_record_status": "active"})

    def action_enderase_reject(self):
        self.write({"enderase_record_status": "rejected"})

    def action_enderase_archive_registry(self):
        self.write({"enderase_record_status": "archived"})
