# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
import logging
import xml.etree.ElementTree as ET

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Maps ODK submission node names (as used by the uploaded Enderase XLSForm) to
# res.partner fields. Choice answers carry lookup *codes* (e.g. ET04, student),
# which resolve to the registry lookups by code.
ENDERASE_ODK_FIELD_MAP = {
    "full_name": "enderase_full_name",
    "fayda_national_id": "fayda_national_id",
    "date_of_birth": "date_of_birth",
    "gender": "gender",
    "nationality": "enderase_nationality",
    "address": "street",
    "admin_region": "enderase_admin_region_id",
    "admin_zone": "enderase_admin_zone_id",
    "admin_woreda": "enderase_admin_woreda_id",
    "kebele_name": "enderase_kebele_name",
    "subcity": "enderase_subcity_id",
    "phone_number": "phone",
    "email_address": "email",
    "occupation_profession": "occupation_profession_id",
    "profession_other": "profession_other",
    "educational_level": "educational_level_id",
    "employment_status": "employment_status_id",
    "current_skills": "current_skills",
    "previous_training_received": "previous_training_received",
    "certifications_held": "certifications_held",
    "desired_training_areas": "desired_training_area_ids",
    "training_area_other": "training_area_other",
    "preferred_training_schedule": "preferred_training_schedule_ids",
    "interested_starting_business": "interested_starting_business",
    "business_area_interest": "business_area_interest",
    "required_support": "required_support_ids",
    "previous_membership": "previous_membership",
    "experience_skill_area": "experience_skill_area",
    "reason_for_joining": "reason_for_joining",
    "interest_areas": "interest_area_ids",
    "interest_area_other": "interest_area_other",
    "why_join": "why_join",
    "career_path": "career_path",
    "skills_to_develop": "skills_to_develop",
    "challenges_faced": "challenges_faced",
    "support_ambitions": "support_ambitions",
    "leadership_growth": "leadership_growth",
    "view_of_enderase": "view_of_enderase",
    "value_to_members_community": "value_to_members_community",
    "hear_about": "hear_about_id",
    "hear_about_other": "hear_about_other",
    "membership_type": "membership_type_id",
    "declaration": "declaration",
}

# res.partner fields a survey question answer can be mapped to. Keeping this an
# explicit, curated list (rather than every partner field) keeps the survey
# designer UI understandable and avoids mapping answers onto internal fields.
ENDERASE_MEMBER_FIELDS = [
    ("enderase_full_name", "Full Name"),
    ("fayda_national_id", "Fayda / National ID"),
    ("phone", "Phone"),
    ("mobile", "Mobile"),
    ("email", "Email"),
    ("gender", "Gender"),
    ("date_of_birth", "Date of Birth"),
    ("enderase_nationality", "Nationality"),
    ("street", "Address"),
    ("enderase_kebele_name", "Kebele"),
    ("enderase_admin_region_id", "Region"),
    ("enderase_admin_zone_id", "Zone"),
    ("enderase_admin_woreda_id", "Woreda"),
    ("enderase_subcity_id", "Subcity"),
    ("occupation_profession_id", "Occupation / Profession"),
    ("profession_other", "Other Occupation / Profession"),
    ("educational_level_id", "Educational Level"),
    ("employment_status_id", "Employment Status"),
    ("current_skills", "Current Skills"),
    ("previous_training_received", "Previous Training Received"),
    ("certifications_held", "Certifications Held"),
    ("desired_training_area_ids", "Desired Training Areas"),
    ("training_area_other", "Other Desired Training Area"),
    ("preferred_training_schedule_ids", "Preferred Training Schedule"),
    ("interested_starting_business", "Interested in Starting a Business"),
    ("business_area_interest", "Business Area of Interest"),
    ("required_support_ids", "Required Support"),
    ("previous_membership", "Previous Membership"),
    ("experience_skill_area", "Experience / Skill Area"),
    ("reason_for_joining", "Reason for Joining"),
    ("interest_area_ids", "Interest Areas"),
    ("interest_area_other", "Other Interest Area"),
    ("why_join", "Why Join"),
    ("career_path", "Career / Life Path"),
    ("skills_to_develop", "Skills / Talents to Develop"),
    ("challenges_faced", "Challenges Faced"),
    ("support_ambitions", "Support for Ambitions"),
    ("leadership_growth", "Leadership Growth"),
    ("view_of_enderase", "View of Enderase"),
    ("value_to_members_community", "Value to Members / Community"),
    ("hear_about_id", "How did you hear about Enderase?"),
    ("hear_about_other", "Other Source"),
    ("membership_type_id", "Membership Type"),
    ("declaration", "Declaration"),
]


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    enderase_creates_member = fields.Boolean(
        string="Register Enderase Member",
        help="When a response is completed (online or imported from ODK), create an "
        "Enderase member from the answers mapped on each question.",
    )


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    enderase_member_field = fields.Selection(
        selection=ENDERASE_MEMBER_FIELDS,
        string="Enderase Member Field",
        help="Store this question's answer on the mapped field of the Enderase member "
        "created when the response is completed.",
    )


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    enderase_member_id = fields.Many2one(
        "res.partner",
        string="Registered Member",
        readonly=True,
        copy=False,
        help="Enderase member created from this survey response.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Only completed responses that already carry answers should provision a
        # member on create. ODK imports create the response first and save the
        # answer lines afterwards, so they are handled by the write() below.
        to_sync = records.filtered(lambda r: r.state == "done" and r.user_input_line_ids)
        if to_sync:
            to_sync._enderase_sync_member()
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get("state") == "done":
            self._enderase_sync_member()
        return res

    def _enderase_sync_member(self):
        for user_input in self:
            if user_input.enderase_member_id or not user_input.survey_id.enderase_creates_member:
                continue
            try:
                user_input._enderase_create_member()
            except Exception as exc:  # noqa: BLE001 - never break survey completion
                _logger.exception(
                    "Failed to create Enderase member for survey response %s: %s",
                    user_input.id,
                    exc,
                )

    def _enderase_create_member(self):
        self.ensure_one()
        if self.enderase_member_id:
            return self.enderase_member_id

        Partner = self.env["res.partner"].sudo()
        vals = {
            "is_registrant": True,
            "is_group": False,
            "is_enderase_member": True,
            "enderase_record_status": "submitted",
            "enderase_membership_status": "applied",
            "rec_import_source_label": "Survey: %s" % (self.survey_id.title or ""),
        }

        # Provenance from ODK when g2p_survey is installed.
        instance_id = getattr(self, "g2p_odk_instance_id", False)
        if instance_id:
            vals["odk_instance_id"] = instance_id
            vals["source_reference"] = instance_id

        vals.update(self._enderase_collect_member_values())

        if not vals.get("name"):
            vals["name"] = vals.get("enderase_full_name") or self.nickname or self.email or "Enderase Member"

        partner = Partner.create(vals)
        self.sudo().write({"enderase_member_id": partner.id})
        return partner

    def _enderase_collect_member_values(self):
        self.ensure_one()
        # An ODK-generated form carries lookup *codes* in its submission XML. When
        # the survey questions declare an ODK field name (g2p_odk_name), map those
        # submission nodes onto member fields by code; otherwise fall back to the
        # per-question answer lines (online / free-text surveys).
        raw_payload = getattr(self, "g2p_odk_raw_payload", False)
        field_map = self._enderase_odk_field_map()
        if raw_payload and field_map:
            return self._enderase_values_from_odk_xml(raw_payload, field_map)
        return self._enderase_values_from_lines()

    def _enderase_odk_field_map(self):
        """Build {ODK submission node name: res.partner field} from the survey.

        Only questions that declare an explicit ODK field name participate, so
        code-based imports apply only to surveys designed for ODK. Falls back to
        the static map for legacy forms with no configured ODK names.
        """
        self.ensure_one()
        mapping = {}
        for question in self.survey_id.question_ids.filtered("enderase_member_field"):
            node = (getattr(question, "g2p_odk_name", "") or "").strip()
            if node:
                mapping[node] = question.enderase_member_field
        return mapping

    def _enderase_values_from_odk_xml(self, xml_content, field_map=None):
        self.ensure_one()
        if field_map is None:
            field_map = dict(ENDERASE_ODK_FIELD_MAP)
        try:
            root = ET.fromstring(xml_content.encode("utf-8"))
        except ET.ParseError:
            return {}
        values_by_name = {}
        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1]
            values_by_name.setdefault(name, (element.text or "").strip())

        partner_fields = self.env["res.partner"]._fields
        result = {}
        for node, field_name in field_map.items():
            raw_value = values_by_name.get(node)
            if not raw_value:
                continue
            field = partner_fields.get(field_name)
            if not field:
                continue
            if field.type == "many2many":
                ids = []
                for code in str(raw_value).split():
                    record_id = self._enderase_match_many2one(field.comodel_name, code)
                    if record_id:
                        ids.append(record_id)
                if ids:
                    result[field_name] = [(6, 0, ids)]
                continue
            coerced = self._enderase_coerce_value(field, raw_value)
            if coerced not in (None, False, ""):
                result[field_name] = coerced

        if result.get("enderase_full_name"):
            result.setdefault("name", result["enderase_full_name"])
        return result

    def _enderase_values_from_lines(self):
        self.ensure_one()
        partner_fields = self.env["res.partner"]._fields
        lines_by_question = {}
        for line in self.user_input_line_ids:
            lines_by_question.setdefault(line.question_id.id, self.env["survey.user_input.line"])
            lines_by_question[line.question_id.id] |= line

        values = {}
        for question in self.survey_id.question_ids.filtered("enderase_member_field"):
            field_name = question.enderase_member_field
            field = partner_fields.get(field_name)
            if not field:
                continue
            raw_value = self._enderase_extract_answer(lines_by_question.get(question.id))
            if raw_value in (None, "", False, []):
                continue
            coerced = self._enderase_coerce_value(field, raw_value)
            if coerced not in (None, False, ""):
                values[field_name] = coerced

        if values.get("enderase_full_name") and "name" not in values:
            values["name"] = values["enderase_full_name"]
        return values

    def _enderase_extract_answer(self, lines):
        if not lines:
            return None
        values = []
        for line in lines:
            if line.skipped:
                continue
            answer_type = line.answer_type
            if answer_type == "char_box":
                values.append(line.value_char_box)
            elif answer_type == "text_box":
                values.append(line.value_text_box)
            elif answer_type == "numerical_box":
                values.append(line.value_numerical_box)
            elif answer_type == "date":
                values.append(line.value_date)
            elif answer_type == "datetime":
                values.append(line.value_datetime)
            elif answer_type == "suggestion":
                answer = line.suggested_answer_id
                # Prefer the ODK code (g2p_survey) so choices resolve to lookups by
                # code; fall back to the human label for plain answers.
                values.append(getattr(answer, "g2p_odk_value", False) or answer.value)
        values = [value for value in values if value not in (None, "", False)]
        if not values:
            return None
        return values if len(values) > 1 else values[0]

    def _enderase_coerce_value(self, field, raw_value):
        if isinstance(raw_value, list):
            raw_value = raw_value[0]
        field_type = field.type
        if field_type in ("char", "text", "html"):
            return str(raw_value)
        if field_type == "boolean":
            return str(raw_value).strip().lower() in ("yes", "true", "1", "agree", "y")
        if field_type in ("date", "datetime"):
            return raw_value
        if field_type == "integer":
            try:
                return int(float(raw_value))
            except (TypeError, ValueError):
                return None
        if field_type == "float":
            try:
                return float(raw_value)
            except (TypeError, ValueError):
                return None
        if field_type == "selection":
            return self._enderase_match_selection(field.name, raw_value)
        if field_type == "many2one":
            return self._enderase_match_many2one(field.comodel_name, raw_value)
        return None

    def _enderase_match_selection(self, field_name, raw_value):
        raw_text = str(raw_value).strip().lower()
        selection = self.env["res.partner"].fields_get([field_name])[field_name].get("selection") or []
        for key, label in selection:
            if raw_text in (str(key).strip().lower(), str(label).strip().lower()):
                return key
        return None

    def _enderase_match_many2one(self, comodel_name, raw_value):
        comodel = self.env[comodel_name].sudo()
        raw_text = str(raw_value).strip()
        # ODK answers carry lookup codes (ET04, student, ...), so match code first;
        # fall back to name for online/free-text answers (e.g. "Oromia").
        if "code" in comodel._fields:
            record = comodel.search([("code", "=ilike", raw_text)], limit=1)
            if record:
                return record.id
        record = comodel.search([("name", "=ilike", raw_text)], limit=1)
        if not record:
            record = comodel.search([("name", "ilike", raw_text)], limit=1)
        return record.id if record else None
