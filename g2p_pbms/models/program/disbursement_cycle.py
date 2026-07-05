from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import datetime


class G2PDisbursementCycle(models.Model):
    _name = "g2p.disbursement.cycle"
    _description = "G2P Disbursement Cycle"
    _rec_name = "cycle_mnemonic"

    cycle_mnemonic = fields.Char(string="Cycle Mnemonic", compute='_compute_cycle_mnemonic', store=True)
    cycle_number = fields.Integer(string="Cycle Sequence", default=0)
    cycle_name = fields.Char(string="Cycle Number", compute='_compute_cycle_name', store=True)
    bridge_envelope_id = fields.Char(string='Bridge Envelope ID')
    program_id = fields.Many2one("g2p.program.definition", string="G2P Program")
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
    current_disbursement_display = fields.Char(
        string="Disbursement", compute="_compute_from_current_list", store=True
    )
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
    target_registry = fields.Selection(related="program_id.target_registry", string="Target Registry Type")
    priority_rule_ids = fields.One2many(
        "g2p.priority.rule.definition", 
        "disbursement_cycle_id", 
        string="Priority Rules"
    )
    beneficiary_list_ids = fields.One2many(
        "g2p.beneficiary.list", 
        "disbursement_cycle_id", 
        string="Beneficiary List"
    )
    envelope_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
        ],
        string="Envelope Creation Status",
        default="pending",
    )
    batch_creation_status = fields.Selection(
        [
            ("not_applicable", "not applicable"),
            ("pending", "pending"),
            ("processing", "processing"),
            ("complete", "complete"),
        ],
        string="Batch Creation Status",
        default="not_applicable",
    )
    approved_for_disbursement = fields.Boolean(string="Approved for Disbursement", default=False)
    creation_date = fields.Datetime(string="Creation Date", default=fields.Datetime.now, readonly=True)

    envelope_creation_latest_error_code = fields.Char(
        string="Envelope Creation Latest Error Code",
        help="Latest error code for envelope creation",
    )
    envelope_creation_attempts = fields.Integer(
        string="Envelope Creation Attempts", default=0
    )
    batch_creation_latest_error_code = fields.Char(
        string="Batch Creation Latest Error Code",
        help="Latest error code for batch creation",
    )
    batch_creation_attempts = fields.Integer(
        string="Batch Creation Attempts", default=0
    )
    disbursement_schedule_date = fields.Date(
        string="Disbursement Schedule Date", required=True, default=fields.Date.today
    )
    envelope_creation_latest_timestamp = fields.Datetime(
        string="Envelope Creation Latest Timestamp"
    )
    batch_creation_latest_timestamp = fields.Datetime(
        string="Batch Creation Latest Timestamp"
    )
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

    @api.depends('cycle_number')
    def _compute_cycle_name(self):
        for rec in self:
            rec.cycle_name = "Cycle %s" % rec.cycle_number if rec.cycle_number else ""

    @api.depends('cycle_number')
    def _compute_cycle_mnemonic(self):
        for rec in self:
            rec.cycle_mnemonic = "Disbursement Cycle %s" % rec.cycle_number if rec.cycle_number else ""

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
        'current_list_id.disbursement_quantity_display',
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
                rec.current_disbursement_display = False
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
            rec.current_disbursement_display = lst.disbursement_quantity_display

    @api.depends('current_list_id.stage_history_ids')
    def _compute_current_stage_history_ids(self):
        for rec in self:
            rec.current_stage_history_ids = rec.current_list_id.stage_history_ids if rec.current_list_id else self.env["g2p.workflow.stage.history"]

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

    @api.depends_context('disbursement_cycle_form_view')
    def _compute_is_readonly(self):
        for rec in self:
            rec.is_readonly = self.env.context.get('disbursement_cycle_form_view', True)

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

    def _calculate_schedule_date(self, program):
        current_str = fields.Datetime.now()
        current = fields.Datetime.from_string(current_str)
        freq = program.disbursement_frequency

        # if freq == 'Daily':
        #     return current.date()

        # elif freq == 'Weekly':
        #     # Compute next occurrence based on configured day of week.
        #     weekday_mapping = {
        #         'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
        #         'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
        #     }
        #     target_weekday = weekday_mapping.get(program.disbursement_day_of_week)
        #     if target_weekday is None:
        #         return current.date()
        #     current_date = current.date()
        #     current_weekday = current_date.weekday()
        #     days_ahead = target_weekday - current_weekday
        #     if days_ahead <= 0:
        #         days_ahead += 7
        #     next_date = current_date + datetime.timedelta(days=days_ahead)
        #     return next_date

        # elif freq == 'Fortnightly':
        #     return (current + datetime.timedelta(days=14)).date()

        # elif freq in ('Monthly', 'BiMonthly', 'Quarterly', 'SemiAnnually', 'Annually'):
        #     increment = 1
        #     if freq == 'BiMonthly':
        #         increment = 2
        #     elif freq == 'Quarterly':
        #         increment = 3
        #     elif freq == 'SemiAnnually':
        #         increment = 6
        #     elif freq == 'Annually':
        #         increment = 12

        #     # Use the disbursement_day_of_month from the program if set; otherwise, use current day.
        #     day = program.disbursement_day_of_month if program.disbursement_day_of_month else current.day
        #     try:
        #         candidate = current.replace(day=day)
        #         if candidate <= current:
        #             candidate = (current + relativedelta(months=increment)).replace(day=day)
        #     except ValueError:
        #         # If the day is invalid, set to the last day of the month.
        #         candidate = (current + relativedelta(months=increment)).replace(day=1) + datetime.timedelta(days=-1)
        #     return candidate.date()

        if freq == 'OnDemand':
            # For on-demand cycles, return current date.
            return current.date()

        else:
            return current.date()


    @api.model
    def create(self, vals):
        if vals.get('program_id'):
            program_id = vals['program_id']
            if not vals.get('cycle_number'):
                last = self.search([('program_id', '=', program_id)], order='cycle_number desc', limit=1)
                vals['cycle_number'] = (last.cycle_number or 0) + 1
            if not vals.get('disbursement_schedule_date'):
                program = self.env['g2p.program.definition'].browse(program_id)
                calculated_date = self._calculate_schedule_date(program)
                if calculated_date:
                    vals['disbursement_schedule_date'] = calculated_date
        record = super(G2PDisbursementCycle, self).create(vals)
        return record
    
    def action_open_create_wizard(self):
        ctx = dict(self.env.context)
        if not ctx.get("default_program_id"):
            if self and self[0].program_id:
                ctx["default_program_id"] = self[0].program_id.id
            elif ctx.get("active_model") == "g2p.program.definition" and ctx.get("active_id"):
                ctx["default_program_id"] = ctx["active_id"]
        return {
            "type": "ir.actions.act_window",
            "name": "New Disbursement Cycle",
            "res_model": "g2p.disbursement.cycle.create.wizard",
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": ctx,
        }

    def action_create_new_list(self):
        self.ensure_one()
        if self.cycle_approved:
            raise UserError("This cycle has been approved and is locked. No further versions can be created.")
        if not self.can_create_list:
            raise UserError("Cannot create a new version while a list is in progress.")
        return {
            "type": "ir.actions.act_window",
            "name": "Create New Disbursement List",
            "res_model": "g2p.beneficiary.list",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_disbursement_cycle_id": self.id,
                "default_list_stage": "disbursement",
                "default_disbursement_schedule_date": self.disbursement_schedule_date,
            },
        }

    def action_refresh_data(self):
        """Force refresh of data from database"""
        self.ensure_one()
        self.invalidate_recordset()
        return self.action_open_view()

    def action_open_view(self):
        self.ensure_one()
        if self.current_list_id:
            return self.current_list_id.action_open_summary_wizard()
        # No list yet — open the summary wizard with Create New Version available
        clean_ctx = {k: v for k, v in self.env.context.items() if not k.startswith("default_")}
        wizard = self.env["g2p.bgtask.summary.wizard"].with_context(clean_ctx).create({
            "disbursement_cycle_id": self.id,
            "disbursement_cycle_m2o_id": self.id,
            "cycle_name": self.cycle_name,
            "cycle_created_on": self.creation_date,
            "cycle_created_by": self.create_uid.id,
            "list_stage": "disbursement",
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

    
    # def action_open_disbursement_envelope_summary_wizard(self):
    #     self.ensure_one()
    #     wizard_vals = {
    #         'disbursement_envelope_id': self.bridge_envelope_id,
    #         "beneficiary_list_id": self.beneficiary_list_id,
    #         "program_mnemonic": self.program_id.program_mnemonic,
    #         "cycle_mnemonic": self.cycle_mnemonic,
    #         "measurement_unit": self.program_id.measurement_unit,
    #     }

    #     wizard = self.env["g2p.disbursement.envelope.summary.wizard"].create(wizard_vals)
    #     return {
    #         "name": "G2P Disbursement Envelope Status Summary",
    #         "view_mode": "form",
    #         "res_model": "g2p.disbursement.envelope.summary.wizard",
    #         "res_id": wizard.id,
    #         "type": "ir.actions.act_window",
    #         "target": "current",
    #         'context': {
    #             'default_disbursement_envelope_id': self.bridge_envelope_id,
    #             'default_beneficiary_list_id': self.beneficiary_list_id,
    #         },
    #     }
