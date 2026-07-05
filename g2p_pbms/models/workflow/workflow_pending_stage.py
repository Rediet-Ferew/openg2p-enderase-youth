from odoo import models, fields, api


class G2PWorkflowPendingStage(models.Model):
    _name = "g2p.workflow.pending.stage"
    _description = "G2P Workflow Pending Stage"
    _order = "enqueued_at asc"

    def _compute_display_name(self):
        for rec in self:
            parts = [
                rec.program_mnemonic or '',
                rec.cycle_name or '',
                rec.list_id.mnemonic or '',
            ]
            rec.display_name = ' / '.join(p for p in parts if p) or rec._description

    list_id = fields.Many2one(
        "g2p.beneficiary.list",
        required=True,
        index=True,
        ondelete="cascade",
        string="Beneficiary List",
    )
    current_stage_id = fields.Many2one(
        "g2p.workflow.stage.definition", required=True, string="Current Stage"
    )
    enqueued_at = fields.Datetime(
        default=fields.Datetime.now, string="Enqueued At"
    )
    stage_status = fields.Selection(
        [("PENDING", "Pending")], default="PENDING", string="Status"
    )

    # --- Related fields for approval queue display ---
    program_id = fields.Many2one(
        "g2p.program.definition", related="list_id.program_id", string="Program"
    )
    program_mnemonic = fields.Char(
        related="list_id.program_id.program_mnemonic", string="Program"
    )
    program_description = fields.Char(
        related="list_id.program_id.description", string="Program Description"
    )
    list_stage = fields.Selection(
        related="list_id.list_stage", string="Type"
    )
    list_number = fields.Integer(
        related="list_id.list_number", string="Current Version"
    )
    number_of_registrants = fields.Integer(
        related="list_id.number_of_registrants", string="# of Beneficiaries"
    )
    current_stage_name = fields.Char(
        related="list_id.current_stage_name", string="Current Stage"
    )
    enrollment_cycle_id = fields.Many2one(
        "g2p.enrollment.cycle", related="list_id.enrollment_cycle_id"
    )
    disbursement_cycle_id = fields.Many2one(
        "g2p.disbursement.cycle", related="list_id.disbursement_cycle_id"
    )

    # --- Computed cycle info ---
    cycle_name = fields.Char(
        string="Cycle #", compute="_compute_cycle_info"
    )
    cycle_created_on = fields.Datetime(
        string="Cycle Created On", compute="_compute_cycle_info"
    )
    cycle_created_by = fields.Many2one(
        "res.users", string="Cycle Created By", compute="_compute_cycle_info"
    )

    # --- History info ---
    previous_stage_name = fields.Char(
        string="Previous Stage", compute="_compute_history_info"
    )
    approved_by = fields.Many2one(
        "res.users", string="Approved By", compute="_compute_history_info"
    )
    approved_at = fields.Datetime(
        string="Approved On", compute="_compute_history_info"
    )

    # --- Computed relational collections for detail view ---
    stage_history_ids = fields.Many2many(
        "g2p.workflow.stage.history",
        compute="_compute_stage_history",
        string="Approval History",
    )
    previous_list_ids = fields.Many2many(
        "g2p.beneficiary.list",
        compute="_compute_previous_lists",
        string="Previous Versions",
    )

    _sql_constraints = [
        (
            "unique_list",
            "UNIQUE(list_id)",
            "Only one pending stage allowed per list.",
        )
    ]

    @api.depends(
        "list_id.enrollment_cycle_id.cycle_name",
        "list_id.enrollment_cycle_id.creation_date",
        "list_id.enrollment_cycle_id.create_uid",
        "list_id.disbursement_cycle_id.cycle_name",
        "list_id.disbursement_cycle_id.creation_date",
        "list_id.disbursement_cycle_id.create_uid",
    )
    def _compute_cycle_info(self):
        for rec in self:
            cycle = rec.list_id.enrollment_cycle_id or rec.list_id.disbursement_cycle_id
            rec.cycle_name = cycle.cycle_name if cycle else False
            rec.cycle_created_on = cycle.creation_date if cycle else False
            rec.cycle_created_by = cycle.create_uid if cycle else False

    @api.depends("list_id.stage_history_ids.acted_at", "list_id.stage_history_ids.status")
    def _compute_history_info(self):
        for rec in self:
            history = rec.list_id.stage_history_ids.sorted("acted_at", reverse=True)
            # Previous stage = last acted stage (most recent)
            rec.previous_stage_name = history[:1].stage_name if history else False
            # Approved by/at = last APPROVED action
            approved = history.filtered(lambda h: h.status == "APPROVED")[:1]
            rec.approved_by = approved.acted_by if approved else False
            rec.approved_at = approved.acted_at if approved else False

    @api.depends("list_id.stage_history_ids")
    def _compute_stage_history(self):
        for rec in self:
            rec.stage_history_ids = rec.list_id.stage_history_ids

    @api.depends("list_id", "enrollment_cycle_id.beneficiary_list_ids", "disbursement_cycle_id.beneficiary_list_ids")
    def _compute_previous_lists(self):
        for rec in self:
            cycle = rec.enrollment_cycle_id or rec.disbursement_cycle_id
            if cycle:
                rec.previous_list_ids = cycle.beneficiary_list_ids.filtered(lambda l: l.id != rec.list_id.id)
            else:
                rec.previous_list_ids = self.env["g2p.beneficiary.list"]

    @api.model
    def _get_approval_queue_stage_ids(self):
        """Return stage IDs that the current user can approve based on their groups."""
        user_groups = self.env.user.groups_id
        all_stages = self.env['g2p.workflow.stage.definition'].search([])
        return [stage.id for stage in all_stages if stage.group_id in user_groups]

    @api.model
    def get_approval_queue_domain(self):
        stage_ids = self._get_approval_queue_stage_ids()
        if not stage_ids:
            return [('id', '=', False)]
        return [('current_stage_id', 'in', stage_ids)]

    def action_approve(self):
        self.ensure_one()
        return self._open_reason_wizard("approve")

    def action_reject(self):
        self.ensure_one()
        return self._open_reason_wizard("reject")

    def _open_reason_wizard(self, action_type):
        wizard = self.env["g2p.approval.reason.wizard"].create({
            "pending_stage_id": self.id,
            "action_type": action_type,
        })
        return {
            "name": "Approve" if action_type == "approve" else "Reject",
            "type": "ir.actions.act_window",
            "res_model": "g2p.approval.reason.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_open_form(self):
        self.ensure_one()
        action = self.list_id.action_open_summary_wizard()
        # Set the pending stage on the wizard so approval buttons appear
        wizard = self.env["g2p.bgtask.summary.wizard"].browse(action["res_id"])
        wizard.write({"pending_stage_id": self.id})
        return action

    def action_open_list_detail(self):
        """Open the beneficiary list summary wizard (Search / API response view)."""
        self.ensure_one()
        return self.list_id.action_open_summary_wizard()
