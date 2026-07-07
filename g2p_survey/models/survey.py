# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import base64
import io
import json
import logging
import re
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from .odk_client import ODKCentralClient

_logger = logging.getLogger(__name__)

XLSFORM_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _slugify(value, prefix="item"):
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", (value or "").strip().lower()).strip("_")
    if not slug:
        slug = prefix
    if slug[0].isdigit():
        slug = f"{prefix}_{slug}"
    return slug


def _local_name(tag):
    return tag.rsplit("}", 1)[-1]


class G2PSurveyOdkServer(models.Model):
    _name = "g2p.survey.odk.server"
    _description = "ODK Central Server"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    base_url = fields.Char(required=True, help="Example: https://central.example.org")
    api_email = fields.Char(required=True)
    api_password = fields.Char(required=True)
    default_project_id = fields.Integer(default=1, required=True)
    timeout = fields.Integer(default=30, required=True)
    verify_ssl = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    last_connection_status = fields.Selection(
        [("ok", "Connected"), ("error", "Failed")],
        readonly=True,
    )
    last_connection_at = fields.Datetime(readonly=True)
    last_error = fields.Text(readonly=True)

    def _get_client(self):
        self.ensure_one()
        return ODKCentralClient(self)

    def action_test_connection(self):
        message = ""
        for server in self:
            try:
                user = server._get_client().get_current_user()
                server.write(
                    {
                        "last_connection_status": "ok",
                        "last_connection_at": fields.Datetime.now(),
                        "last_error": False,
                    }
                )
                message = "Connected to ODK Central as %s." % (
                    user.get("email") or user.get("displayName") or "the API user"
                )
            except Exception as exc:
                server.write(
                    {
                        "last_connection_status": "error",
                        "last_connection_at": fields.Datetime.now(),
                        "last_error": str(exc),
                    }
                )
                raise
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "ODK Central",
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }


class SurveyQuestion(models.Model):
    _inherit = "survey.question"

    g2p_odk_name = fields.Char(
        string="ODK Field Name",
        help="Column name used for this question in the generated XLSForm (survey sheet "
        "'name'). Also becomes the submission node name. Leave empty to auto-generate a "
        "slug. Use short snake_case identifiers (e.g. admin_region).",
    )
    g2p_odk_appearance = fields.Char(
        string="ODK Appearance",
        help="XLSForm 'appearance' column (e.g. multiline, minimal, field-list).",
    )
    g2p_odk_relevant = fields.Char(
        string="ODK Relevant",
        help="XLSForm 'relevant' expression controlling when this question is shown, "
        "e.g. ${occupation_profession}='other'.",
    )
    g2p_odk_constraint = fields.Char(
        string="ODK Constraint",
        help="XLSForm 'constraint' expression, e.g. . <= today().",
    )
    g2p_odk_constraint_message = fields.Char(string="ODK Constraint Message")
    g2p_odk_choice_model = fields.Char(
        string="ODK Choice Model",
        help="Technical model name to build this select's choices from at push time "
        "(e.g. g2p.enderase.admin.region). The choice value is taken from the value "
        "field (default 'code') and the label from the label field (default 'name').",
    )
    g2p_odk_choice_domain = fields.Char(
        string="ODK Choice Domain",
        default="[]",
        help="Optional Odoo domain (as text) filtering the choice model records.",
    )
    g2p_odk_choice_value_field = fields.Char(
        string="ODK Choice Value Field",
        default="code",
        help="Field on the choice model used as the stored XLSForm choice value.",
    )
    g2p_odk_choice_label_field = fields.Char(
        string="ODK Choice Label Field",
        default="name",
        help="Field on the choice model used as the displayed XLSForm choice label.",
    )
    g2p_odk_choice_order = fields.Char(
        string="ODK Choice Order",
        help="Optional order (ORM order string) for the choice model records.",
    )
    g2p_odk_choice_filter_column = fields.Char(
        string="ODK Choice Filter Column",
        help="Extra column added to the choices sheet holding the parent code used for a "
        "cascading select (e.g. region_code on a zone list).",
    )
    g2p_odk_choice_parent_path = fields.Char(
        string="ODK Choice Parent Path",
        help="Dotted path on the choice model returning the parent code used to fill the "
        "filter column (e.g. region_id.code).",
    )
    g2p_odk_choice_filter_parent = fields.Char(
        string="ODK Choice Filter Parent",
        help="ODK field name of the parent question referenced by the cascade filter "
        "(e.g. admin_region). Produces choice_filter: <filter column>=${<parent>}.",
    )

    def _g2p_sync_odk_choices_from_model(self):
        """(Re)build suggested answers of model-backed choice questions from the model.

        ODK generation reads the choice model directly at push time, but the native
        Odoo (online) survey widget needs stored ``survey.question.answer`` records to
        render options. This copies each lookup record as an answer (label = the
        model's label field, ODK value = the model's code) so the same survey works
        both online and offline. Safe to re-run whenever the lookup data changes.
        """
        for question in self:
            if not question.g2p_odk_choice_model or question.question_type not in (
                "simple_choice",
                "multiple_choice",
            ):
                continue
            model = self.env[question.g2p_odk_choice_model.strip()].sudo()
            try:
                domain = safe_eval(question.g2p_odk_choice_domain or "[]")
            except Exception:  # noqa: BLE001
                domain = []
            records = model.search(domain, order=question.g2p_odk_choice_order or None)
            value_field = (question.g2p_odk_choice_value_field or "code").strip()
            label_field = (question.g2p_odk_choice_label_field or "name").strip()
            question.suggested_answer_ids.unlink()
            answers = []
            for index, record in enumerate(records, start=1):
                code = str(record[value_field] or "").strip()
                if not code:
                    continue
                answers.append(
                    (0, 0, {
                        "sequence": index,
                        "value": str(record[label_field] or code).strip(),
                        "g2p_odk_value": code,
                    })
                )
            if answers:
                question.write({"suggested_answer_ids": answers})


class SurveyQuestionAnswer(models.Model):
    _inherit = "survey.question.answer"

    g2p_odk_value = fields.Char(
        string="ODK Value",
        help="Explicit XLSForm choice value (name column) for this answer, e.g. yes/no. "
        "Leave empty to auto-generate a slug.",
    )


class SurveySurvey(models.Model):
    _inherit = "survey.survey"

    g2p_odk_delivery_mode = fields.Selection(
        [
            ("online", "Odoo Online"),
            ("offline", "ODK Offline"),
            ("both", "Online and ODK"),
        ],
        default="both",
        required=True,
        string="Delivery Mode",
    )
    g2p_odk_server_id = fields.Many2one("g2p.survey.odk.server", string="ODK Server")
    g2p_odk_project_id = fields.Integer(string="ODK Project ID")
    g2p_odk_project_name = fields.Char(
        string="ODK Project Name",
        help="If set, the survey is pushed to the ODK Central project with this name. "
        "The project is created on the server if it does not exist yet, and its ID is "
        "stored back on ODK Project ID.",
    )
    g2p_odk_xml_form_id = fields.Char(string="ODK Form ID", copy=False)
    g2p_odk_version = fields.Char(string="ODK Version", copy=False)
    g2p_odk_state = fields.Selection(
        [("not_pushed", "Not Pushed"), ("draft", "Draft"), ("open", "Open"), ("closed", "Closed")],
        default="not_pushed",
        copy=False,
        string="ODK State",
    )
    g2p_odk_published_at = fields.Char(string="ODK Published At", readonly=True, copy=False)
    g2p_odk_last_sync_at = fields.Datetime(string="Last ODK Push", readonly=True, copy=False)
    g2p_odk_last_import_at = fields.Datetime(string="Last ODK Import", readonly=True, copy=False)
    g2p_odk_last_error = fields.Text(string="Last ODK Error", readonly=True, copy=False)
    @api.onchange("g2p_odk_server_id")
    def _onchange_g2p_odk_server_id(self):
        if self.g2p_odk_server_id and not self.g2p_odk_project_id:
            self.g2p_odk_project_id = self.g2p_odk_server_id.default_project_id

    def action_g2p_sync_odk_choices(self):
        """Populate model-backed select questions with stored answers.

        Makes the online Odoo survey render the same options that ODK builds from
        the lookup models at push time.
        """
        count = 0
        for survey in self:
            questions = survey.question_ids.filtered("g2p_odk_choice_model")
            questions._g2p_sync_odk_choices_from_model()
            count += len(questions)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "ODK Choices",
                "message": "Synced choices for %s question(s) from their models." % count,
                "type": "success",
                "sticky": False,
            },
        }

    def action_g2p_push_to_odk(self):
        for survey in self:
            if not survey.g2p_odk_server_id:
                raise UserError("Select an ODK server before pushing this survey.")
            if survey.g2p_odk_delivery_mode == "online":
                raise UserError("Set Delivery Mode to ODK Offline or Online and ODK before pushing.")

            version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            survey._g2p_check_odk_supported_questions()
            xml_form_id = survey.g2p_odk_xml_form_id or survey._g2p_default_odk_form_id()
            xlsx_content = survey._g2p_build_odk_xlsform(xml_form_id, version)
            client = survey.g2p_odk_server_id._get_client()
            project_id = survey._g2p_resolve_odk_project(client)
            try:
                # Upload the XLSForm as a draft, then publish it. ODK Central
                # converts the XLSForm to an XForm via pyxform server-side. The
                # XLSForm is always generated from the survey questions, never
                # stored or attached on the survey.
                client.push_form_xlsx(project_id, xml_form_id, xlsx_content, publish=False)
                result = client.publish_form_draft(project_id, xml_form_id, version=version)
                result = result or {}
                survey.write(
                    {
                        "g2p_odk_project_id": project_id,
                        "g2p_odk_xml_form_id": result.get("xmlFormId") or xml_form_id,
                        "g2p_odk_version": result.get("version") or version,
                        "g2p_odk_state": result.get("state") or "open",
                        "g2p_odk_published_at": result.get("publishedAt"),
                        "g2p_odk_last_sync_at": fields.Datetime.now(),
                        "g2p_odk_last_error": False,
                    }
                )
            except Exception as exc:
                survey.write(
                    {
                        "g2p_odk_last_sync_at": fields.Datetime.now(),
                        "g2p_odk_last_error": str(exc),
                    }
                )
                raise

    def action_g2p_import_odk_submissions(self):
        total_imported = 0
        total_skipped = 0
        for survey in self:
            if not survey.g2p_odk_server_id:
                raise UserError("Select an ODK server before importing submissions.")
            if not survey.g2p_odk_xml_form_id:
                raise UserError("Push this survey to ODK before importing submissions.")
            imported, skipped = survey._g2p_import_odk_submissions(raise_on_error=True)
            total_imported += imported
            total_skipped += skipped

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "ODK Submissions",
                "message": "Imported %s submission(s), skipped %s existing/invalid submission(s)."
                % (total_imported, total_skipped),
                "type": "success",
                "sticky": False,
            },
        }

    def _g2p_import_odk_submissions(self, raise_on_error=False):
        """Import new ODK submissions for a single survey.

        Returns a ``(imported, skipped)`` tuple. Existing submissions are looked
        up in a single query (no per-submission query), and only genuinely new
        submissions trigger an XML/attachment download.
        """
        self.ensure_one()
        UserInput = self.env["survey.user_input"].sudo()
        project_id = self._g2p_get_odk_project_id()
        client = self.g2p_odk_server_id._get_client()
        imported = 0
        skipped = 0
        try:
            submissions = client.list_form_submissions(project_id, self.g2p_odk_xml_form_id)
            # Prefetch every already-imported instance id in one query.
            existing_ids = set(
                UserInput.search([("survey_id", "=", self.id)]).mapped("g2p_odk_instance_id")
            )
            for submission in submissions:
                instance_id = submission.get("instanceId")
                if submission.get("deletedAt") or not instance_id or instance_id in existing_ids:
                    skipped += 1
                    continue

                xml_content = client.get_submission_xml(
                    project_id,
                    self.g2p_odk_xml_form_id,
                    instance_id,
                )
                parsed_answers = self._g2p_parse_odk_submission_xml(xml_content)
                user_input = self._g2p_create_user_input_from_odk(
                    submission,
                    xml_content,
                    parsed_answers,
                )
                self._g2p_import_submission_attachments(client, project_id, instance_id, user_input)
                existing_ids.add(instance_id)
                imported += 1

            self.write(
                {
                    "g2p_odk_last_import_at": fields.Datetime.now(),
                    "g2p_odk_last_error": False,
                }
            )
        except Exception as exc:
            self.write(
                {
                    "g2p_odk_last_import_at": fields.Datetime.now(),
                    "g2p_odk_last_error": str(exc),
                }
            )
            if raise_on_error:
                raise
            _logger.warning("ODK import failed for survey %s: %s", self.id, exc)
        return imported, skipped

    def _g2p_import_submission_attachments(self, client, project_id, instance_id, user_input):
        """Download a submission's media attachments and store them on the response."""
        self.ensure_one()
        try:
            attachments = client.list_submission_attachments(
                project_id, self.g2p_odk_xml_form_id, instance_id
            )
        except Exception as exc:
            _logger.warning("Could not list ODK attachments for %s: %s", instance_id, exc)
            return
        Attachment = self.env["ir.attachment"].sudo()
        for meta in attachments:
            if not meta.get("exists", True):
                continue
            filename = meta.get("name")
            if not filename:
                continue
            try:
                content, content_type = client.download_submission_attachment(
                    project_id, self.g2p_odk_xml_form_id, instance_id, filename
                )
            except Exception as exc:
                _logger.warning("Could not download ODK attachment %s: %s", filename, exc)
                continue
            Attachment.create(
                {
                    "name": filename,
                    "raw": content,
                    "mimetype": content_type,
                    "res_model": "survey.user_input",
                    "res_id": user_input.id,
                }
            )

    @api.model
    def _g2p_cron_import_odk_submissions(self):
        """Scheduled import for all ODK-enabled, pushed surveys."""
        surveys = self.search(
            [
                ("g2p_odk_delivery_mode", "in", ["offline", "both"]),
                ("g2p_odk_server_id", "!=", False),
                ("g2p_odk_xml_form_id", "!=", False),
            ]
        )
        for survey in surveys:
            survey._g2p_import_odk_submissions(raise_on_error=False)
        return True

    def action_g2p_assign_odk_app_users(self):
        for survey in self:
            users = self.env["g2p.survey.odk.user"].search(
                [
                    ("user_type", "=", "app_user"),
                    ("state", "=", "created"),
                    ("survey_ids", "in", survey.id),
                ]
            )
            users.action_assign_to_surveys()

    def _g2p_get_odk_project_id(self):
        self.ensure_one()
        project_id = self.g2p_odk_project_id or self.g2p_odk_server_id.default_project_id
        if not project_id:
            raise UserError("Set an ODK project ID on the survey or ODK server.")
        return project_id

    def _g2p_resolve_odk_project(self, client):
        """Resolve (and if needed create) the ODK project to push this survey to.

        Preference order: a configured project ID that exists on the server, then a
        project matching ``g2p_odk_project_name`` (created if missing), then the ODK
        server's default project. The resolved ID is stored back on the survey.
        """
        self.ensure_one()
        if self.g2p_odk_project_id and client.get_project(self.g2p_odk_project_id):
            return self.g2p_odk_project_id

        name = (self.g2p_odk_project_name or "").strip()
        if name:
            project = client.find_project_by_name(name) or client.create_project(name)
            project_id = project.get("id")
            if not project_id:
                raise UserError("ODK Central did not return a project id for %r." % name)
            self.write({"g2p_odk_project_id": project_id})
            return project_id

        default = self.g2p_odk_server_id.default_project_id
        if default and client.get_project(default):
            self.write({"g2p_odk_project_id": default})
            return default

        raise UserError(
            "ODK project %s does not exist on the server. Set an 'ODK Project Name' to "
            "auto-create a project, or enter a valid 'ODK Project ID'."
            % (self.g2p_odk_project_id or default or "(none)")
        )

    def _g2p_default_odk_form_id(self):
        self.ensure_one()
        return "survey_%s_%s" % (self.id, _slugify(self.title, prefix="form"))

    def _g2p_odk_questions(self):
        self.ensure_one()
        return self.question_ids.filtered(lambda question: not question.is_page).sorted("sequence")

    def _g2p_check_odk_supported_questions(self):
        self.ensure_one()
        questions = self._g2p_odk_questions()
        if not questions:
            raise UserError("Add at least one question before pushing this survey to ODK.")
        unsupported = questions.filtered(lambda question: question.question_type == "matrix")
        if unsupported:
            raise UserError(
                "ODK export does not support matrix questions yet: %s"
                % ", ".join(unsupported.mapped("title"))
            )

    def _g2p_odk_question_name(self, question):
        if question.g2p_odk_name:
            return question.g2p_odk_name.strip()
        return "q_%s_%s" % (question.id, _slugify(question.title, prefix="question"))

    def _g2p_odk_answer_value(self, answer):
        if answer.g2p_odk_value:
            return answer.g2p_odk_value.strip()
        return "a_%s_%s" % (answer.id, _slugify(answer.value, prefix="answer"))

    def _g2p_odk_choice_list_name(self, question):
        return "choices_%s" % self._g2p_odk_question_name(question)

    def _g2p_odk_xlsform_type(self, question):
        base_types = {
            "char_box": "text",
            "text_box": "text",
            "numerical_box": "decimal",
            "date": "date",
            "datetime": "dateTime",
        }
        if question.question_type == "simple_choice":
            return "select_one %s" % self._g2p_odk_choice_list_name(question)
        if question.question_type == "multiple_choice":
            return "select_multiple %s" % self._g2p_odk_choice_list_name(question)
        return base_types.get(question.question_type, "text")

    @staticmethod
    def _g2p_odk_resolve_path(record, path):
        """Follow a dotted field path on ``record`` (e.g. region_id.code)."""
        value = record
        for part in (path or "").split("."):
            if not part:
                continue
            value = value[part]
        return value

    def _g2p_odk_choice_rows(self, question, list_name):
        """Return (rows, filter_column) for a choice question.

        Model-backed choices are read from ``g2p_odk_choice_model`` at push time so
        the XLSForm always reflects the current lookup records (value = code,
        label = name). Cascading selects add a ``filter_column`` holding the parent
        code. Otherwise choices come from the question's suggested answers.
        """
        rows = []
        filter_column = None
        if question.g2p_odk_choice_model:
            model_name = question.g2p_odk_choice_model.strip()
            Model = self.env[model_name].sudo()
            try:
                domain = safe_eval(question.g2p_odk_choice_domain or "[]")
            except Exception:  # noqa: BLE001 - fall back to no filter on bad domain
                domain = []
            records = Model.search(domain, order=question.g2p_odk_choice_order or None)
            value_field = (question.g2p_odk_choice_value_field or "code").strip()
            label_field = (question.g2p_odk_choice_label_field or "name").strip()
            filter_column = (question.g2p_odk_choice_filter_column or "").strip() or None
            parent_path = question.g2p_odk_choice_parent_path
            for record in records:
                row = {
                    "list_name": list_name,
                    "name": str(record[value_field] or "").strip(),
                    "label": str(record[label_field] or "").strip(),
                }
                if filter_column and parent_path:
                    row[filter_column] = str(self._g2p_odk_resolve_path(record, parent_path) or "").strip()
                if row["name"]:
                    rows.append(row)
            return rows, filter_column

        for answer in question.suggested_answer_ids.sorted("sequence"):
            rows.append(
                {
                    "list_name": list_name,
                    "name": self._g2p_odk_answer_value(answer),
                    "label": answer.value or "",
                }
            )
        return rows, None

    def _g2p_build_odk_xlsform(self, xml_form_id, version):
        """Build an XLSForm (.xlsx) definition for this survey.

        ODK Central converts XLSForms to XForms via pyxform on upload, so this is
        the authoring format we push. Choices for select questions are generated
        from the configured Odoo model (``g2p_odk_choice_model``) using the record
        ``code`` as the value, and support cascading selects (Region -> Zone ->
        Woreda) via ``choice_filter``. Question and choice names reuse the same
        identifiers as the submission parser so imported answers resolve.
        """
        self.ensure_one()
        questions = self._g2p_odk_questions()

        # First pass: collect all choice rows so we know the full set of cascade
        # filter columns before writing the (single) choices sheet header.
        all_choice_rows = []
        filter_columns = []
        for question in questions:
            if question.question_type not in ("simple_choice", "multiple_choice"):
                continue
            list_name = self._g2p_odk_choice_list_name(question)
            rows, filter_column = self._g2p_odk_choice_rows(question, list_name)
            all_choice_rows.extend(rows)
            if filter_column and filter_column not in filter_columns:
                filter_columns.append(filter_column)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        survey_sheet = workbook.add_worksheet("survey")
        survey_headers = [
            "type",
            "name",
            "label",
            "required",
            "hint",
            "relevant",
            "constraint",
            "constraint_message",
            "choice_filter",
            "appearance",
        ]
        for col, header in enumerate(survey_headers):
            survey_sheet.write(0, col, header)

        choices_sheet = workbook.add_worksheet("choices")
        choices_headers = ["list_name", "name", "label"] + filter_columns
        for col, header in enumerate(choices_headers):
            choices_sheet.write(0, col, header)

        survey_row = 1
        for question in questions:
            hint = ""
            if question.description:
                hint = re.sub("<[^>]*>", "", question.description).strip()
            appearance = question.g2p_odk_appearance or (
                "multiline" if question.question_type == "text_box" else ""
            )
            choice_filter = ""
            if question.g2p_odk_choice_filter_column and question.g2p_odk_choice_filter_parent:
                choice_filter = "%s=${%s}" % (
                    question.g2p_odk_choice_filter_column.strip(),
                    question.g2p_odk_choice_filter_parent.strip(),
                )
            survey_sheet.write_row(
                survey_row,
                0,
                [
                    self._g2p_odk_xlsform_type(question),
                    self._g2p_odk_question_name(question),
                    question.title or self._g2p_odk_question_name(question),
                    "yes" if question.constr_mandatory else "",
                    hint,
                    question.g2p_odk_relevant or "",
                    question.g2p_odk_constraint or "",
                    question.g2p_odk_constraint_message or "",
                    choice_filter,
                    appearance,
                ],
            )
            survey_row += 1

        choices_row = 1
        for row in all_choice_rows:
            choices_sheet.write_row(
                choices_row,
                0,
                [row.get(header, "") for header in choices_headers],
            )
            choices_row += 1

        settings_sheet = workbook.add_worksheet("settings")
        settings_sheet.write_row(0, 0, ["form_title", "form_id", "version"])
        settings_sheet.write_row(1, 0, [self.title or xml_form_id, xml_form_id, version])

        workbook.close()
        return output.getvalue()

    def _g2p_submission_datetime(self, submission):
        value = (
            (submission.get("currentVersion") or {}).get("createdAt")
            or submission.get("createdAt")
        )
        if not value:
            return fields.Datetime.now()
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            return fields.Datetime.now()

    def _g2p_parse_odk_submission_xml(self, xml_content):
        self.ensure_one()
        try:
            root = ET.fromstring(xml_content.encode("utf-8"))
        except ET.ParseError as exc:
            raise UserError("Could not parse ODK submission XML: %s" % exc) from exc

        values_by_name = {}
        for element in root.iter():
            values_by_name.setdefault(_local_name(element.tag), (element.text or "").strip())

        answers = {}
        for question in self._g2p_odk_questions():
            raw_value = values_by_name.get(self._g2p_odk_question_name(question), "")
            if question.question_type == "multiple_choice":
                answers[question.id] = [item for item in raw_value.split() if item]
            else:
                answers[question.id] = raw_value
        return answers

    def _g2p_create_user_input_from_odk(self, submission, xml_content, parsed_answers):
        self.ensure_one()
        submitted_at = self._g2p_submission_datetime(submission)
        submitter = submission.get("submitter") or {}
        user_input = self.env["survey.user_input"].sudo().create(
            {
                "survey_id": self.id,
                "state": "done",
                "start_datetime": submitted_at,
                "end_datetime": submitted_at,
                "nickname": submitter.get("displayName") or False,
                "g2p_response_source": "odk",
                "g2p_odk_instance_id": submission.get("instanceId"),
                "g2p_odk_submitter_id": submission.get("submitterId"),
                "g2p_odk_device_id": submission.get("deviceId"),
                "g2p_odk_submission_meta": json.dumps(submission, ensure_ascii=False, indent=2),
                "g2p_odk_raw_payload": xml_content,
            }
        )
        for question in self._g2p_odk_questions():
            self._g2p_save_odk_answer(user_input, question, parsed_answers.get(question.id))
        user_input.write({"state": "done", "survey_first_submitted": True})
        return user_input

    def _g2p_save_odk_answer(self, user_input, question, value):
        # Model-backed choices carry lookup codes with no matching survey answer
        # record; the Enderase member importer reads them from the raw XML, so
        # skip trying to save a per-question line for them.
        if question.g2p_odk_choice_model and question.question_type in (
            "simple_choice",
            "multiple_choice",
        ):
            return
        if question.question_type == "simple_choice":
            answer = self._g2p_find_choice_answer(question, value)
            user_input._save_lines(question, str(answer.id) if answer else False)
            return
        if question.question_type == "multiple_choice":
            answer_ids = [
                str(answer.id)
                for answer in (self._g2p_find_choice_answer(question, item) for item in (value or []))
                if answer
            ]
            user_input._save_lines(question, answer_ids)
            return
        if question.question_type == "datetime" and value:
            value = self._g2p_to_odoo_datetime(value)
        elif question.question_type == "date" and value:
            value = value[:10]
        user_input._save_lines(question, value or False)

    def _g2p_find_choice_answer(self, question, odk_value):
        if not odk_value:
            return self.env["survey.question.answer"]
        normalized = str(odk_value).strip()
        for answer in question.suggested_answer_ids:
            if normalized in {
                self._g2p_odk_answer_value(answer),
                str(answer.id),
                _slugify(answer.value, prefix="answer"),
                (answer.value or "").strip(),
            }:
                return answer
        return self.env["survey.question.answer"]

    def _g2p_to_odoo_datetime(self, value):
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return value
        if parsed.tzinfo:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return fields.Datetime.to_string(parsed)


class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    g2p_response_source = fields.Selection(
        [("odoo", "Odoo Online"), ("odk", "ODK Offline")],
        default="odoo",
        required=True,
        string="Source",
        readonly=True,
    )
    g2p_odk_instance_id = fields.Char(string="ODK Instance ID", readonly=True, copy=False)
    g2p_odk_submitter_id = fields.Integer(string="ODK Submitter ID", readonly=True, copy=False)
    g2p_odk_device_id = fields.Char(string="ODK Device ID", readonly=True, copy=False)
    g2p_odk_submission_meta = fields.Text(string="ODK Submission Metadata", readonly=True, copy=False)
    g2p_odk_raw_payload = fields.Text(string="ODK Submission XML", readonly=True, copy=False)
    g2p_odk_attachment_count = fields.Integer(
        string="ODK Media", compute="_compute_g2p_odk_attachment_count"
    )

    _sql_constraints = [
        (
            "g2p_odk_instance_unique",
            "unique(survey_id, g2p_odk_instance_id)",
            "This ODK submission has already been imported for this survey.",
        ),
    ]

    def _compute_g2p_odk_attachment_count(self):
        Attachment = self.env["ir.attachment"].sudo()
        counts = {
            group["res_id"]: group["res_id_count"]
            for group in Attachment.read_group(
                [("res_model", "=", "survey.user_input"), ("res_id", "in", self.ids)],
                ["res_id"],
                ["res_id"],
            )
        }
        for record in self:
            record.g2p_odk_attachment_count = counts.get(record.id, 0)

    def action_g2p_view_odk_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "ODK Media",
            "res_model": "ir.attachment",
            "view_mode": "kanban,tree,form",
            "domain": [("res_model", "=", "survey.user_input"), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": "survey.user_input",
                "default_res_id": self.id,
            },
        }


class G2PSurveyOdkUser(models.Model):
    _name = "g2p.survey.odk.user"
    _description = "ODK Survey User"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    user_type = fields.Selection(
        [("staff", "Staff User"), ("app_user", "ODK Collect App User")],
        default="app_user",
        required=True,
        tracking=True,
    )
    email = fields.Char()
    password = fields.Char()
    server_id = fields.Many2one("g2p.survey.odk.server", required=True, tracking=True)
    project_id = fields.Integer()
    actor_id = fields.Integer(readonly=True)
    token = fields.Char(readonly=True, copy=False)
    form_role = fields.Selection(
        [("app-user", "App User"), ("formfill", "Data Collector"), ("manager", "Manager")],
        default="app-user",
        required=True,
    )
    survey_ids = fields.Many2many(
        "survey.survey",
        "g2p_survey_odk_user_survey_rel",
        "odk_user_id",
        "survey_id",
        string="Allowed Surveys",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("created", "Created in ODK"), ("revoked", "Revoked")],
        default="draft",
        required=True,
        tracking=True,
    )
    last_sync_at = fields.Datetime(readonly=True)
    last_error = fields.Text(readonly=True)
    g2p_odk_config_url = fields.Char(
        string="ODK Collect Server URL",
        compute="_compute_g2p_odk_config",
        help="Token-scoped ODK Central URL an ODK Collect device uses for this app user.",
    )
    g2p_odk_qr_code = fields.Binary(
        string="ODK Collect QR",
        compute="_compute_g2p_odk_config",
        help="Scan from ODK Collect (Configure via QR code) to auto-configure the device.",
    )

    @api.onchange("server_id")
    def _onchange_server_id(self):
        if self.server_id and not self.project_id:
            self.project_id = self.server_id.default_project_id

    @api.constrains("user_type", "email")
    def _check_email_for_staff(self):
        for user in self:
            if user.user_type == "staff" and not user.email:
                raise ValidationError("Staff users require an email address.")

    @api.depends("token", "user_type", "state", "server_id.base_url", "project_id", "name")
    def _compute_g2p_odk_config(self):
        for user in self:
            url = False
            qr = False
            if (
                user.user_type == "app_user"
                and user.state == "created"
                and user.token
                and user.server_id.base_url
            ):
                base = (user.server_id.base_url or "").rstrip("/")
                project_id = user.project_id or user.server_id.default_project_id
                url = "%s/v1/key/%s/projects/%s" % (base, user.token, project_id)
                qr = user._g2p_build_odk_collect_qr(url)
            user.g2p_odk_config_url = url
            user.g2p_odk_qr_code = qr

    def _g2p_build_odk_collect_qr(self, server_url):
        """Build the base64 PNG of an ODK Collect settings QR code.

        ODK Collect expects a QR encoding zlib-compressed, base64-encoded settings
        JSON. See https://docs.getodk.org/collect-import-export/.
        """
        self.ensure_one()
        settings = {
            "general": {
                "server_url": server_url,
                "form_update_mode": "match_exactly",
                "autosend": "wifi_and_cellular",
            },
            "admin": {},
            "project": {"name": self.name or "Enderase", "color": "#3e6957", "icon": "E"},
        }
        payload = base64.b64encode(
            zlib.compress(json.dumps(settings).encode("utf-8"))
        ).decode("ascii")
        try:
            png = self.env["ir.actions.report"].barcode(
                "QR", payload, width=300, height=300, humanreadable=0
            )
        except Exception as exc:  # pragma: no cover - depends on reportlab QR support
            _logger.warning("Could not render ODK Collect QR for user %s: %s", self.id, exc)
            return False
        return base64.b64encode(png)

    def action_create_in_odk(self):
        for user in self:
            client = user.server_id._get_client()
            project_id = user.project_id or user.server_id.default_project_id
            try:
                if user.user_type == "staff":
                    result = client.create_user(user.email, user.password, user.name)
                else:
                    result = client.create_app_user(project_id, user.name)
                user.write(
                    {
                        "actor_id": result.get("id"),
                        "token": result.get("token"),
                        "project_id": result.get("projectId") or project_id,
                        "state": "created",
                        "last_sync_at": fields.Datetime.now(),
                        "last_error": False,
                    }
                )
                user.message_post(body="Created in ODK Central (actor %s)." % result.get("id"))
            except Exception as exc:
                user.write(
                    {
                        "last_sync_at": fields.Datetime.now(),
                        "last_error": str(exc),
                    }
                )
                raise

    def action_assign_to_surveys(self):
        for user in self:
            if not user.actor_id:
                raise UserError("Create the user in ODK before assigning survey access.")
            client = user.server_id._get_client()
            for survey in user.survey_ids:
                if not survey.g2p_odk_xml_form_id:
                    raise UserError("Push survey %s to ODK before assigning users." % survey.title)
                project_id = (
                    survey.g2p_odk_project_id
                    or user.project_id
                    or user.server_id.default_project_id
                )
                client.assign_form_role(
                    project_id,
                    survey.g2p_odk_xml_form_id,
                    user.form_role,
                    user.actor_id,
                )
            user.write({"last_sync_at": fields.Datetime.now(), "last_error": False})

    def action_revoke(self):
        for user in self:
            if user.user_type != "app_user" or not user.actor_id:
                raise UserError("Only ODK Collect app users created in ODK can be revoked.")
            client = user.server_id._get_client()
            project_id = user.project_id or user.server_id.default_project_id
            try:
                client.revoke_app_user(project_id, user.actor_id)
                user.write(
                    {
                        "state": "revoked",
                        "token": False,
                        "last_sync_at": fields.Datetime.now(),
                        "last_error": False,
                    }
                )
                user.message_post(body="App user revoked in ODK Central.")
            except Exception as exc:
                user.write({"last_sync_at": fields.Datetime.now(), "last_error": str(exc)})
                raise
