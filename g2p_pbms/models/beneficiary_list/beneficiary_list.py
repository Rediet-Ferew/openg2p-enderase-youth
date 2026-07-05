import json
import uuid
from odoo import models, fields, api
from odoo.exceptions import UserError


class G2PBeneficiaryList(models.Model):
    _name = "g2p.beneficiary.list"
    _description = "G2P Beneficiary List"
    _rec_name = "mnemonic"

    beneficiary_list_id = fields.Char(string='Beneficiary List ID', readonly=True, required=True, default=lambda self: str(uuid.uuid4()))
    mnemonic = fields.Char(string="Mnemonic")
    program_id = fields.Many2one("g2p.program.definition", string="G2P Program", compute="_compute_program_id", store=True, readonly=True)
    enrollment_cycle_id = fields.Many2one("g2p.enrollment.cycle", string="Enrollment Cycle", required=False)
    disbursement_cycle_id = fields.Many2one("g2p.disbursement.cycle", string="Disbursement Cycle", required=False)

    brief = fields.Text(string="Brief")
    brief_truncated = fields.Char(string="Brief", compute="_compute_brief_truncated", store=False)

    # Cycle detail fields (non-editable) — displayed in Create Version popup
    cycle_name_display = fields.Char(string="Cycle", compute="_compute_cycle_details", store=False)
    cycle_creation_date = fields.Datetime(string="Cycle Creation Date", compute="_compute_cycle_details", store=False)
    next_list_number = fields.Integer(string="List #", compute="_compute_next_list_number", store=False)
    disbursement_schedule_date = fields.Date(string="Disbursement Schedule Date")

    eligibility_process_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Eligibility Process Status",
        default="pending",
    )
    eligibility_number_of_attempts = fields.Integer(string="Eligibility Number of Attempts", default=0)
    eligibility_latest_error_code = fields.Char(string="Eligibility Latest Error Code", default=None)
    eligibility_processed_date = fields.Datetime(string="Eligibility Processed Date", default=None)

    entitlement_process_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Entitlement Process Status",
        default="not_applicable",
    )
    entitlement_number_of_attempts = fields.Integer(string="Entitlement Number of Attempts", default=0)
    entitlement_latest_error_code = fields.Char(string="Entitlement Latest Error Code", default=None)
    entitlement_processed_date = fields.Datetime(string="Entitlement Processed Date", default=None)

    envelope_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Disbursement Envelope Status",
        default="not_applicable",
    )
    envelope_creation_number_of_attempts = fields.Integer(string="Envelope Creation Number of Attempts", default=0)
    envelope_creation_latest_error_code = fields.Char(string="Envelope Creation Latest Error Code", default=None)
    envelope_creation_processed_date = fields.Datetime(string="Envelope Creation Processed Date", default=None)

    disbursement_batch_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
            ("failed", "failed")
        ],
        string="Disbursement Batch Creation Status",
        default="not_applicable",
    )
    dbc_number_of_attempts = fields.Integer(string="Disbursement Batch Creation Number of Attempts", default=0)
    dbc_latest_error_code = fields.Char(string="Disbursement Batch Creation Latest Error Code", default=None)
    dbc_processed_date = fields.Datetime(string="Disbursement Batch Creation Processed Date", default=None)

    number_of_registrants = fields.Integer(string="Number of Registrants", default=0)
    number_of_entitlements_processed = fields.Integer(string="Number of Entitlements Processed", default=0)

    list_stage = fields.Selection(
        [
            ("enrollment", "ENROLLMENT"),
            ("disbursement", "DISBURSEMENT")
        ],
        string="List Stage",
    )

    # --- Approval workflow fields ---
    workflow_approval_status = fields.Selection(
        [
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        string="Approval Status",
        default="PENDING",
        index=True,
    )
    pending_stage_ids = fields.One2many(
        "g2p.workflow.pending.stage", "list_id", string="Pending Stage"
    )
    stage_history_ids = fields.One2many(
        "g2p.workflow.stage.history", "list_id", string="Stage History"
    )
    current_stage_name = fields.Char(
        string="Current Stage",
        compute="_compute_current_stage_name",
        store=False,
    )
    current_stage_number = fields.Integer(
        string="Stage #",
        compute="_compute_current_stage_name",
        store=False,
    )

    # --- Deprecated fields kept for backward compatibility ---
    approval_date = fields.Date(string="Approval Date", default=None, readonly=True)
    list_workflow_status = fields.Selection(
        [
            ("initiated", ""),
            ("approved_final_enrolment", "APPROVED FINAL ENROLMENT"),
            ("approved_for_disbursement", "APPROVED FOR DISBURSEMENT"),
        ],
        string="List Workflow Status",
        default="initiated",
    )
    verification_ids = fields.One2many(
        "storage.file",
        "beneficiary_list_id",
        string="Community Verification",
    )

    list_number = fields.Integer(string="List Number", readonly=True, default=0)
    disbursement_quantity = fields.Char(
        string="Disbursement Quantity (JSON)",
        help="JSON string of disbursement quantities per benefit code.",
    )
    disbursement_quantity_display = fields.Char(
        string="Disbursement",
        compute="_compute_disbursement_quantity_display",
        store=False,
    )
    latest_stage_history_id = fields.Many2one(
        "g2p.workflow.stage.history",
        string="Latest Stage History",
        compute="_compute_latest_stage_history",
        store=True,
    )
    final_stage_number = fields.Integer(
        string="Final Stage #",
        related="latest_stage_history_id.stage_number",
        store=False,
    )
    final_stage_name = fields.Char(
        string="Final Stage",
        related="latest_stage_history_id.stage_name",
        store=False,
    )
    final_acted_by = fields.Many2one(
        "res.users",
        string="Final Acted By",
        related="latest_stage_history_id.acted_by",
        store=False,
    )
    final_acted_at = fields.Datetime(
        string="Final Acted At",
        related="latest_stage_history_id.acted_at",
        store=False,
    )

    creation_date = fields.Datetime(string="Creation Date", default=fields.Datetime.now, readonly=True)
    processed_date = fields.Datetime(string="Processed Date", default=None, readonly=True)

    def _compute_brief_truncated(self):
        for rec in self:
            if rec.brief and len(rec.brief) > 50:
                rec.brief_truncated = rec.brief[:50] + "..."
            else:
                rec.brief_truncated = rec.brief or ""

    @api.depends('enrollment_cycle_id', 'disbursement_cycle_id')
    def _compute_cycle_details(self):
        for rec in self:
            if rec.enrollment_cycle_id:
                rec.cycle_name_display = rec.enrollment_cycle_id.cycle_name or ""
                rec.cycle_creation_date = rec.enrollment_cycle_id.creation_date or False
            elif rec.disbursement_cycle_id:
                rec.cycle_name_display = rec.disbursement_cycle_id.cycle_name or ""
                rec.cycle_creation_date = rec.disbursement_cycle_id.creation_date or False
            else:
                rec.cycle_name_display = ""
                rec.cycle_creation_date = False

    @api.depends('enrollment_cycle_id', 'disbursement_cycle_id')
    def _compute_next_list_number(self):
        for rec in self:
            if rec.enrollment_cycle_id:
                # Calculate next version for enrollment
                count = self.search_count([('enrollment_cycle_id', '=', rec.enrollment_cycle_id.id)])
                rec.next_list_number = count + 1
            elif rec.disbursement_cycle_id:
                # Calculate next version for disbursement
                count = self.search_count([('disbursement_cycle_id', '=', rec.disbursement_cycle_id.id)])
                rec.next_list_number = count + 1
            else:
                rec.next_list_number = 0

    def _compute_disbursement_quantity_display(self):
        for rec in self:
            if not rec.disbursement_quantity:
                rec.disbursement_quantity_display = False
                continue
            try:
                data = json.loads(rec.disbursement_quantity)
                if isinstance(data, list) and data:
                    first = data[0]
                    qty = first.get('quantity') or first.get('total_disbursement_quantity') or ''
                    unit = first.get('unit') or first.get('measurement_unit') or ''
                    rec.disbursement_quantity_display = "%s %s" % (qty, unit) if unit else str(qty)
                elif isinstance(data, dict):
                    items = list(data.values())
                    rec.disbursement_quantity_display = str(items[0]) if items else False
                else:
                    rec.disbursement_quantity_display = str(data)
            except Exception:
                rec.disbursement_quantity_display = rec.disbursement_quantity

    @api.depends('stage_history_ids.acted_at')
    def _compute_latest_stage_history(self):
        for rec in self:
            history = rec.stage_history_ids.sorted('id', reverse=True)
            rec.latest_stage_history_id = history[:1] or False

    @api.depends("pending_stage_ids.current_stage_id")
    def _compute_current_stage_name(self):
        for rec in self:
            pending = rec.pending_stage_ids[:1]
            if pending and rec.workflow_approval_status == "PENDING":
                rec.current_stage_name = pending.current_stage_id.stage_name
                rec.current_stage_number = pending.current_stage_id.stage_number
            else:
                rec.current_stage_name = False
                rec.current_stage_number = 0

    @api.depends('enrollment_cycle_id.program_id', 'disbursement_cycle_id.program_id')
    def _compute_program_id(self):
        for record in self:
            if record.enrollment_cycle_id:
                record.program_id = record.enrollment_cycle_id.program_id
                record.list_stage = "enrollment"
            elif record.disbursement_cycle_id:
                record.program_id = record.disbursement_cycle_id.program_id
                record.list_stage = "disbursement"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.enrollment_cycle_id:
                rec.list_number = self.search_count([('enrollment_cycle_id', '=', rec.enrollment_cycle_id.id)])
            elif rec.disbursement_cycle_id:
                rec.list_number = self.search_count([('disbursement_cycle_id', '=', rec.disbursement_cycle_id.id)])
            if not rec.mnemonic:
                rec.mnemonic = "Version %s" % rec.list_number
            rec._initialize_workflow()
        return records

    def _initialize_workflow(self):
        """Create the initial pending stage record for this list."""
        self.ensure_one()
        if not self.program_id:
            return
        cycle_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"
        first_stage = self.env["g2p.workflow.stage.definition"].search(
            [
                ("program_id", "=", self.program_id.id),
                ("cycle_type", "=", cycle_type),
            ],
            order="stage_number asc",
            limit=1,
        )
        if first_stage:
            now = fields.Datetime.now()
            self.env["g2p.workflow.pending.stage"].create({
                "list_id": self.id,
                "current_stage_id": first_stage.id,
                "enqueued_at": now,
                "stage_status": "PENDING",
            })
            self.env["g2p.workflow.stage.history"].sudo().create({
                "list_id": self.id,
                "list_type": cycle_type,
                "stage_id": first_stage.id,
                "enqueued_at": now,
                "status": "PENDING",
            })
            self.workflow_approval_status = "PENDING"

    def action_approve_stage(self, reason=None):
        """Approve the current pending stage; advance to next or mark APPROVED."""
        self.ensure_one()
        pending = self.pending_stage_ids[:1]
        if not pending:
            raise UserError("No pending stage found for this list.")
        if self.workflow_approval_status != "PENDING":
            raise UserError("List is not in PENDING status.")

        current_stage = pending.current_stage_id
        list_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"

        # Update existing PENDING history record, or create if missing (backward compat)
        existing_history = self.env["g2p.workflow.stage.history"].search([
            ("list_id", "=", self.id),
            ("stage_id", "=", current_stage.id),
            ("status", "=", "PENDING"),
        ], limit=1)
        history_vals = {
            "acted_by": self.env.user.id,
            "acted_at": fields.Datetime.now(),
            "status": "APPROVED",
            "reason": reason,
        }
        if existing_history:
            existing_history.write(history_vals)
        else:
            self.env["g2p.workflow.stage.history"].create({
                "list_id": self.id,
                "list_type": list_type,
                "stage_id": current_stage.id,
                "enqueued_at": pending.enqueued_at,
                **history_vals,
            })

        # if current_stage.is_final_stage:
        #     pending.unlink()
        #     self.workflow_approval_status = "APPROVED"
        #     self.list_workflow_status = (
        #         "approved_final_enrolment" if self.list_stage == "enrollment"
        #         else "approved_for_disbursement"
        #     )
        #     self.approval_date = fields.Date.context_today(self)
        # else:
        next_stage = self.env["g2p.workflow.stage.definition"].search(
            [
                ("program_id", "=", self.program_id.id),
                ("cycle_type", "=", current_stage.cycle_type),
                ("stage_number", ">", current_stage.stage_number),
            ],
            order="stage_number asc",
            limit=1,
        )
        if next_stage:
            now = fields.Datetime.now()
            pending.write({
                "current_stage_id": next_stage.id,
                "enqueued_at": now,
            })
            self.env["g2p.workflow.stage.history"].sudo().create({
                "list_id": self.id,
                "list_type": list_type,
                "stage_id": next_stage.id,
                "enqueued_at": now,
                "status": "PENDING",
            })
        else:
            pending.unlink()
            self.workflow_approval_status = "APPROVED"
            self.list_workflow_status = (
                "approved_final_enrolment" if self.list_stage == "enrollment"
                else "approved_for_disbursement"
            )
            self.envelope_creation_status = (
                "pending" if self.list_stage == "disbursement" 
                else "not_applicable"
            )
            self.approval_date = fields.Date.context_today(self)


    def action_reject_stage(self, reason=None):
        """Reject the current pending stage; mark list REJECTED."""
        self.ensure_one()
        pending = self.pending_stage_ids[:1]
        if not pending:
            raise UserError("No pending stage found for this list.")
        if self.workflow_approval_status != "PENDING":
            raise UserError("List is not in PENDING status.")

        current_stage = pending.current_stage_id
        list_type = "ENROLMENT" if self.list_stage == "enrollment" else "DISBURSEMENT"

        # Update existing PENDING history record, or create if missing (backward compat)
        existing_history = self.env["g2p.workflow.stage.history"].search([
            ("list_id", "=", self.id),
            ("stage_id", "=", current_stage.id),
            ("status", "=", "PENDING"),
        ], limit=1)
        history_vals = {
            "acted_by": self.env.user.id,
            "acted_at": fields.Datetime.now(),
            "status": "REJECTED",
            "reason": reason,
        }
        if existing_history:
            existing_history.write(history_vals)
        else:
            self.env["g2p.workflow.stage.history"].create({
                "list_id": self.id,
                "list_type": list_type,
                "stage_id": current_stage.id,
                "enqueued_at": pending.enqueued_at,
                **history_vals,
            })
        pending.unlink()
        self.workflow_approval_status = "REJECTED"

    def action_view_stage_history(self):
        self.ensure_one()
        return {
            "name": "%s - Approval History" % self.mnemonic,
            "type": "ir.actions.act_window",
            "res_model": "g2p.workflow.stage.history",
            "view_mode": "tree",
            "domain": [("list_id", "=", self.id)],
            "target": "new",
            "context": {"create": False, "delete": False},
        }

    def _get_rules_cycle_id(self):
        """Return the disbursement cycle ID to use for displaying priority rules.
        For old (non-current) cycles with no rules, fall back to the latest cycle's rules."""
        dc = self.disbursement_cycle_id
        if not dc:
            return False
        if dc.is_current_cycle or dc.priority_rule_ids:
            return dc.id
        latest = self.env["g2p.disbursement.cycle"].search(
            [("program_id", "=", self.program_id.id)],
            order="cycle_number desc",
            limit=1,
        )
        return latest.id if latest else dc.id

    def action_open_summary_wizard(self):
        if (
            self.list_stage == 'enrollment'
            and self.list_workflow_status != 'approved_final_enrollment'
            and getattr(self.program_id, 'auto_approve_enrolment', False)
            and getattr(self.program_id, 'verifications_for_enrolment', 0) == 0
        ):
            self.list_workflow_status = 'approved_final_enrolment'
            self.approval_date = fields.Date.context_today(self)
            if self.enrollment_cycle_id:
                self.env['g2p.enrollment.cycle'].browse(self.enrollment_cycle_id.id).write({
                    'approved_for_enrollment': True,
                })

        if (
            self.list_stage == 'disbursement'
            and self.list_workflow_status != 'approved_for_disbursement'
            and getattr(self.program_id, 'auto_approve_disbursement', False)
            and getattr(self.program_id, 'verifications_for_disbursement', 0) == 0
        ):
            self.list_workflow_status = 'approved_for_disbursement'
            self.approval_date = fields.Date.context_today(self)
            if self.disbursement_cycle_id:
                self.env['g2p.disbursement.cycle'].browse(self.disbursement_cycle_id.id).write({
                    'approved_for_disbursement': True,
                })

        self.ensure_one()
        cycle = self.enrollment_cycle_id or self.disbursement_cycle_id
        latest_history = self.latest_stage_history_id
        pending = self.pending_stage_ids[:1]
        wizard_vals = {
            "target_registry": self.program_id.target_registry,
            "mnemonic": self.mnemonic,
            "brief": self.brief,
            "program_id": self.program_id.id,
            "beneficiary_list_id": self.id,
            "beneficiary_list_uuid": self.beneficiary_list_id,
            "enrollment_cycle_id": self.enrollment_cycle_id.id if self.enrollment_cycle_id else False,
            "disbursement_cycle_id": self.disbursement_cycle_id.id if self.disbursement_cycle_id else False,
            "disbursement_cycle_m2o_id": self._get_rules_cycle_id(),
            "list_stage": self.list_stage,
            "list_workflow_status": self.list_workflow_status,
            "enrollment_start_date": self.enrollment_cycle_id.enrollment_start_date if self.enrollment_cycle_id else None,
            "enrollment_end_date": self.enrollment_cycle_id.enrollment_end_date if self.enrollment_cycle_id else None,
            "disbursement_cycle_mnemonic": self.disbursement_cycle_id.cycle_mnemonic if self.disbursement_cycle_id else None,
            "approved_for_disbursement": self.disbursement_cycle_id.approved_for_disbursement if self.disbursement_cycle_id else None,
            # Cycle context for the unified view
            "cycle_name": cycle.cycle_name if cycle else False,
            "cycle_created_on": cycle.creation_date if cycle else False,
            "cycle_created_by": cycle.create_uid.id if cycle else False,
            "current_version": self.list_number,
            "current_stage_display": self.current_stage_name if self.workflow_approval_status == 'PENDING' else (latest_history.stage_name if latest_history else False),
            "current_approval_status": self.workflow_approval_status,
            "current_acted_at": latest_history.acted_at if latest_history else False,
            "current_acted_by": latest_history.acted_by.id if latest_history else False,
            "can_create_list": self.workflow_approval_status == 'REJECTED',
            # New fields for workflow and beneficiaries section
            "current_enqueued_at": pending.enqueued_at if pending else (latest_history.enqueued_at if latest_history else False),
            "current_beneficiary_count": self.number_of_registrants,
            "eligibility_process_status": self.eligibility_process_status,
            # Beneficiary extra fields
            "computation_status": self.entitlement_process_status or "not_applicable",
            "total_entitlements": self.number_of_entitlements_processed,
            # Bridge Status fields
            "envelope_status": self.envelope_creation_status,
            "disbursement_batch_status": self.disbursement_batch_creation_status
        }

        wizard = self.env["g2p.bgtask.summary.wizard"].create(wizard_vals)
        return {
            "name": "%s / %s" % (self.program_id.program_mnemonic, cycle.cycle_name) if cycle else "Beneficiary List",
            "view_mode": "form",
            "res_model": "g2p.bgtask.summary.wizard",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "current",
            'context': {
                'default_target_registry': self.program_id.target_registry,
                'default_program_id': self.program_id.id,
                'default_beneficiary_list_id': self.beneficiary_list_id,
            },
        }

    def action_save_and_open_summary(self):
        """Called from the create form footer button — record already saved by Odoo.
        Redirect main window to the fresh summary wizard for this new list."""
        self.ensure_one()
        return self.action_open_summary_wizard()
