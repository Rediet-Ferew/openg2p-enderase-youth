from odoo import fields, models


class G2PYouthRegistry(models.Model):
    _name = "g2p.youth.registry"
    _description = "Enderase Youth Registry"
    _inherit = "g2p.registry"
    _rec_name = "record_name"

    internal_record_id = fields.Char(string="Enderase Registry ID", index=True)
    functional_record_id = fields.Char(string="Functional Record ID", index=True)
    record_name = fields.Char(string="Name", index=True)
    is_group = fields.Boolean(string="Group")
    is_registrant = fields.Boolean(string="Registrant")
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
        string="Record Status",
    )
    enderase_membership_status = fields.Selection(
        [
            ("not_member", "Not Member"),
            ("applied", "Applied"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("rejected", "Rejected"),
        ],
        string="Membership Status",
    )
    enderase_beneficiary_category = fields.Selection(
        [("individual", "Individual"), ("group", "Group")],
        string="Beneficiary Category",
    )
    enderase_beneficiary_type = fields.Selection(
        [
            ("member", "Member"),
            ("group", "Group"),
            ("startup", "Startup"),
            ("service_recipient", "Service Recipient"),
            ("representative", "Representative"),
        ],
        string="Beneficiary Type",
    )
    fayda_national_id = fields.Char(string="Fayda/National ID", index=True)
    date_of_birth = fields.Date(string="Date of Birth")
    gender = fields.Selection([("male", "Male"), ("female", "Female"), ("other", "Other")])
    enderase_nationality = fields.Char(string="Nationality")
    enderase_admin_region_id = fields.Integer(string="Region")
    enderase_admin_zone_id = fields.Integer(string="Zone")
    enderase_admin_woreda_id = fields.Integer(string="Woreda")
    enderase_kebele_name = fields.Char(string="Kebele Name")
    enderase_subcity_id = fields.Integer(string="Subcity")
    occupation_profession_id = fields.Integer(string="Occupation/Profession")
    profession_other = fields.Char(string="Other Occupation/Profession")
    educational_level_id = fields.Integer(string="Educational Level")
    employment_status_id = fields.Integer(string="Employment Status")
    current_skills = fields.Text(string="Current Skills")
    previous_training_received = fields.Text(string="Previous Training Received")
    certifications_held = fields.Text(string="Certifications Held")
    interested_starting_business = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Interested in starting a business?",
    )
    business_area_interest = fields.Char(string="Business Area of Interest")
    previous_membership = fields.Char(string="Previous Membership")
    experience_skill_area = fields.Text(string="Experience or Skill Area")
    reason_for_joining = fields.Text(string="Reason for Joining")
    why_join = fields.Text(string="Why Join")
    career_path = fields.Text(string="Career or Life Path")
    skills_to_develop = fields.Text(string="Skills or Talents to Develop")
    challenges_faced = fields.Text(string="Challenges Faced")
    support_ambitions = fields.Text(string="Support for Ambitions")
    leadership_growth = fields.Text(string="Leadership Growth")
    view_of_enderase = fields.Text(string="View of Enderase")
    value_to_members_community = fields.Text(string="Value to Members and Community")
    hear_about_id = fields.Integer(string="How Did You Hear About Enderase?")
    hear_about_other = fields.Char(string="Other Source")
    membership_type_id = fields.Integer(string="Membership Type")
    declaration = fields.Selection([("agree", "Agree"), ("disagree", "Disagree")])
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
    odk_instance_id = fields.Char(string="ODK Instance ID", index=True)
