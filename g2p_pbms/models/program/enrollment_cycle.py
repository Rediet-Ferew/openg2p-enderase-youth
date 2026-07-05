from odoo import models, fields, api
from odoo.exceptions import UserError


class G2PEnrollmentCycle(models.Model):
    _name = "g2p.enrollment.cycle"
    _description = "G2P Enrollment Cycle"
    _rec_name = "cycle_mnemonic"

    enrollment_cycle_id = fields.Char(string='Enrollment Cycle ID')
    cycle_number = fields.Integer(string="Cycle Sequence", default=0)
    cycle_name = fields.Char(string="Cycle Number")
    cycle_mnemonic = fields.Char(string="Enrollment Cycle Mnemonic", compute='_compute_cycle_mnemonic', store=True)
    program_id = fields.Many2one("g2p.program.definition", string="G2P Program")
    creation_date = fields.Datetime(string="Creation Date", default=fields.Datetime.now, readonly=True)

    current_list_id = fields.Many2one(
        "g2p.beneficiary.list",
        string="Current List",
        compute="_compute_current_list",
        store=True,
    )
    number_of_lists = fields.Integer(
        string="Number of Lists",
        compute="_compute_number_of_lists",
        store=True,
    )

    # Derived from current_list_id for display
    current_stage_display = fields.Char(
        string="Stage", compute="_compute_from_current_list", store=True
    )
    current_beneficiary_count = fields.Integer(
        string="# of Beneficiaries", compute="_compute_from_current_list", store=True
    )
    current_approval_status = fields.Selection(
        [("PENDING", "Pending"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")],
        string="Status", compute="_compute_from_current_list", store=True,
    )
    current_acted_at = fields.Datetime(
        string="Acted On", compute="_compute_from_current_list", store=True
    )
    current_enqueued_at = fields.Datetime(
        string="Enqueued On", compute="_compute_from_current_list", store=True
    )
    current_acted_by = fields.Many2one(
        "res.users", string="Acted By", compute="_compute_from_current_list", store=True
    )
    can_create_list = fields.Boolean(
        compute="_compute_from_current_list", store=False
    )
    cycle_approved = fields.Boolean(
        string="Cycle Approved", compute="_compute_from_current_list", store=True
    )
    current_stage_history_ids = fields.Many2many(
        "g2p.workflow.stage.history",
        compute="_compute_current_stage_history_ids",
        string="Approval History",
    )
    beneficiary_list_ids = fields.One2many(
        "g2p.beneficiary.list", "enrollment_cycle_id", string="Beneficiary Lists"
    )

    # Date fields made optional (no longer required)
    enrollment_start_date = fields.Date(string="Enrollment Start Date")
    enrollment_end_date = fields.Date(string="Enrollment End Date")
    disbursement_start_date = fields.Date(string="Disbursement Start Date")
    disbursement_end_date = fields.Date(string="Disbursement End Date")

    # Deprecated: kept for backward compatibility
    approved_for_enrollment = fields.Boolean(string="Approved for Enrollment", default=False)

    is_readonly = fields.Boolean(compute='_compute_is_readonly', store=False)
    is_current_cycle = fields.Boolean(
        compute='_compute_is_current_cycle', store=False
    )

    # WIP and count computed fields
    wip_list_id = fields.Many2one(
        "g2p.beneficiary.list",
        string="WIP List",
        compute="_compute_wip_and_counts",
        store=False,
    )
    wip_stage_name = fields.Char(
        string="Current Stage",
        compute="_compute_wip_and_counts",
        store=False,
    )
    list_count = fields.Integer(
        string="# Lists",
        compute="_compute_wip_and_counts",
        store=False,
    )
    list_count_display = fields.Char(
        string="# Lists",
        compute="_compute_wip_and_counts",
        store=False,
    )
    approved_count = fields.Integer(
        string="# Approved",
        compute="_compute_wip_and_counts",
        store=False,
    )
    pending_count = fields.Integer(
        string="# Pending",
        compute="_compute_wip_and_counts",
        store=False,
    )
    has_wip_list = fields.Boolean(
        string="Has WIP List",
        compute="_compute_wip_and_counts",
        store=False,
    )
    number_of_lists_display = fields.Char(
        string="# of Versions",
        compute="_compute_number_of_lists_display",
        store=False,
    )

    _sql_constraints = [
        (
            'cycle_number_program_id_unique',
            'unique(cycle_number, program_id)',
            'Cycle Number must be unique per Program.'
        ),
    ]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        program_id = res.get('program_id') or self.env.context.get('default_program_id')
        if program_id:
            last = self.search(
                [('program_id', '=', program_id)],
                order='cycle_number desc',
                limit=1,
            )
            next_number = (last.cycle_number or 0) + 1
            res['cycle_number'] = next_number
            if not res.get('cycle_name'):
                res['cycle_name'] = "Cycle %s" % next_number
        return res

    @api.depends('cycle_number')
    def _compute_cycle_mnemonic(self):
        for rec in self:
            rec.cycle_mnemonic = "Enrollment Cycle %s" % rec.cycle_number if rec.cycle_number else ""

    @api.depends('beneficiary_list_ids.creation_date')
    def _compute_current_list(self):
        for rec in self:
            lists = rec.beneficiary_list_ids.sorted('creation_date', reverse=True)
            rec.current_list_id = lists[:1] or False

    @api.depends('beneficiary_list_ids')
    def _compute_number_of_lists(self):
        for rec in self:
            rec.number_of_lists = len(rec.beneficiary_list_ids)

    @api.depends(
        'is_current_cycle',
        'current_list_id.workflow_approval_status',
        'current_list_id.current_stage_name',
        'current_list_id.number_of_registrants',
        'current_list_id.latest_stage_history_id.stage_name',
        'current_list_id.latest_stage_history_id.acted_at',
        'current_list_id.latest_stage_history_id.acted_by',
        'current_list_id.pending_stage_ids.enqueued_at',
    )
    def _compute_from_current_list(self):
        for rec in self:
            lst = rec.current_list_id
            if not lst:
                rec.current_stage_display = False
                rec.current_beneficiary_count = 0
                rec.current_approval_status = False
                rec.current_acted_at = False
                rec.current_enqueued_at = False
                rec.current_acted_by = False
                rec.can_create_list = rec.is_current_cycle
                rec.cycle_approved = False
                continue
            rec.current_beneficiary_count = lst.number_of_registrants
            rec.current_approval_status = lst.workflow_approval_status
            history = lst.latest_stage_history_id
            rec.current_acted_at = history.acted_at if history else False
            rec.current_acted_by = history.acted_by if history else False
            if lst.workflow_approval_status == 'PENDING':
                pending = lst.pending_stage_ids[:1]
                rec.current_stage_display = lst.current_stage_name
                rec.current_enqueued_at = pending.enqueued_at if pending else False
            else:
                rec.current_stage_display = history.stage_name if history else False
                rec.current_enqueued_at = history.enqueued_at if history else False
            approved = lst.workflow_approval_status == 'APPROVED'
            rec.can_create_list = rec.is_current_cycle and lst.workflow_approval_status == 'REJECTED'
            rec.cycle_approved = approved

    @api.depends('current_list_id.stage_history_ids')
    def _compute_current_stage_history_ids(self):
        for rec in self:
            rec.current_stage_history_ids = rec.current_list_id.stage_history_ids if rec.current_list_id else self.env["g2p.workflow.stage.history"]

    @api.depends_context('enrollment_cycle_form_view')
    def _compute_is_readonly(self):
        for rec in self:
            rec.is_readonly = self.env.context.get('enrollment_cycle_form_view', True)

    @api.depends('program_id', 'cycle_number')
    def _compute_is_current_cycle(self):
        for rec in self:
            if rec.program_id and rec.cycle_number:
                latest = self.search(
                    [('program_id', '=', rec.program_id.id)],
                    order='cycle_number desc',
                    limit=1,
                )
                rec.is_current_cycle = latest.id == rec.id
            else:
                rec.is_current_cycle = False

    @api.depends('number_of_lists')
    def _compute_number_of_lists_display(self):
        for rec in self:
            rec.number_of_lists_display = str(rec.number_of_lists) if rec.number_of_lists else ''

    @api.depends("beneficiary_list_ids.workflow_approval_status", "beneficiary_list_ids.current_stage_name")
    def _compute_wip_and_counts(self):
        for rec in self:
            lists = rec.beneficiary_list_ids
            rec.list_count = len(lists)
            rec.list_count_display = str(rec.list_count) if rec.list_count else ''
            rec.approved_count = len(lists.filtered(lambda l: l.workflow_approval_status == "APPROVED"))
            pending_lists = lists.filtered(lambda l: l.workflow_approval_status == "PENDING")
            rec.pending_count = len(pending_lists)
            wip = pending_lists[:1]
            rec.wip_list_id = wip or False
            rec.wip_stage_name = wip.current_stage_name if wip else False
            rec.has_wip_list = bool(wip)

    def action_open_create_wizard(self):
        ctx = dict(self.env.context)
        if not ctx.get("default_program_id"):
            # When called from O2M control button inside a program form
            if self and self[0].program_id:
                ctx["default_program_id"] = self[0].program_id.id
            elif ctx.get("active_model") == "g2p.program.definition" and ctx.get("active_id"):
                ctx["default_program_id"] = ctx["active_id"]
        return {
            "type": "ir.actions.act_window",
            "name": "New Enrolment Cycle",
            "res_model": "g2p.enrollment.cycle.create.wizard",
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": ctx,
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('program_id'):
                program_id = vals['program_id']
                if not vals.get('cycle_number'):
                    last = self.search([('program_id', '=', program_id)], order='cycle_number desc', limit=1)
                    vals['cycle_number'] = (last.cycle_number or 0) + 1
                if not vals.get('cycle_name'):
                    vals['cycle_name'] = "Cycle %s" % vals['cycle_number']
        records = super().create(vals_list)
        return records

    def _check_wip_list(self):
        """Raise if a WIP list already exists for this cycle."""
        self.ensure_one()
        wip = self.beneficiary_list_ids.filtered(
            lambda l: l.workflow_approval_status == "PENDING"
        )
        if wip:
            raise UserError(
                "A list is already in progress (%s). Complete or reject it before creating a new one." % wip[0].mnemonic
            )

    def action_refresh_data(self):
        self.ensure_one()
        self.invalidate_recordset()
        return self.action_open_view()

    def action_create_new_list(self):
        self.ensure_one()
        if self.cycle_approved:
            raise UserError("This cycle has been approved and is locked. No further versions can be created.")
        if not self.can_create_list:
            raise UserError("Cannot create a new version while a list is in progress.")
        return {
            "type": "ir.actions.act_window",
            "name": "Create New Enrolment List",
            "res_model": "g2p.beneficiary.list",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_enrollment_cycle_id": self.id,
                "default_list_stage": "enrollment",
            },
        }

    def action_open_view(self):
        self.ensure_one()
        if self.current_list_id:
            return self.current_list_id.action_open_summary_wizard()
        # No list yet — open the summary wizard with Create New Version available
        clean_ctx = {k: v for k, v in self.env.context.items() if not k.startswith("default_")}
        wizard = self.env["g2p.bgtask.summary.wizard"].with_context(clean_ctx).create({
            "enrollment_cycle_id": self.id,
            "cycle_name": self.cycle_name,
            "cycle_created_on": self.creation_date,
            "cycle_created_by": self.create_uid.id,
            "list_stage": "enrollment",
            "program_id": self.program_id.id if self.program_id else False,
            "target_registry": self.program_id.target_registry if self.program_id else False,
            "can_create_list": True,
        })
        return {
            "name": "%s / %s" % (self.program_id.program_mnemonic, self.cycle_name) if self.program_id else self.cycle_name,
            "view_mode": "form",
            "res_model": "g2p.bgtask.summary.wizard",
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "target": "current",
        }
