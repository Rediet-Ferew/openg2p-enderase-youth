from odoo import models, fields, api
from odoo.addons.g2p_registry_type_addon.models import G2PRegistryType


class G2PProgramDefinition(models.Model):
    _name = "g2p.program.definition"
    _description = "G2P Program Definition"
    _table = "g2p_program_definition"
    _rec_name = "program_mnemonic"

    program_mnemonic = fields.Char(string="Program Mnemonic", required=True)
    description = fields.Char(string="Description")
    target_registry = fields.Selection(
        selection=G2PRegistryType.selection(), string="Target Registry", required=True
    )
    program_status = fields.Selection(
        [
            ("ACTIVE", "Active"),
            ("PAUSED", "Paused"),
            ("CLOSED", "Closed"),
        ],
        string="Program Status",
        required=True,
    )
    benefit_code_ids = fields.Many2many(
        'g2p.benefit.codes',
        compute='_compute_benefit_code_ids',
        string="Benefit Codes"
    )
    program_benefit_code_ids = fields.One2many(
        'g2p.program.benefit.codes', 'program_id', string="Program Benefit Codes"
    )
    eligibility_rule_ids = fields.One2many(
        'g2p.eligibility.rule.definition', 'program_id', string="Eligibility Rules"
    )
    entitlement_rule_ids = fields.One2many(
        'g2p.entitlement.rule.definition', 'program_id', string="Entitlement Rules"
    )
    beneficiary_list_ids = fields.One2many(
        "g2p.beneficiary.list",
        "program_id",
        string="Eligibility Request Queue",
    )
    enrollment_cycle_ids = fields.One2many(
        "g2p.enrollment.cycle",
        "program_id",
        string="Enrollment Cycle",
    )
    latest_enrollment_cycle = fields.Char(
        string="Latest Enrollment Cycle",
        compute="_compute_latest_enrollment_cycle",
        store=False,
    )
    latest_enrollment_cycle_id = fields.Many2one(
        "g2p.enrollment.cycle",
        string="Latest Enrollment Cycle Record",
        compute="_compute_latest_enrollment_cycle_id",
        store=False,
    )
    latest_ec_cycle_name = fields.Char(
        related="latest_enrollment_cycle_id.cycle_name",
        string="Current Cycle",
        store=False,
    )
    latest_ec_version = fields.Char(
        related="latest_enrollment_cycle_id.current_list_id.mnemonic",
        string="Current Version",
        store=False,
    )
    latest_ec_stage = fields.Char(
        related="latest_enrollment_cycle_id.current_stage_display",
        string="Current Stage",
        store=False,
    )
    latest_ec_status = fields.Selection(
        related="latest_enrollment_cycle_id.current_approval_status",
        string="Current Status",
        store=False,
    )
    latest_ec_creation_date = fields.Datetime(
        related="latest_enrollment_cycle_id.creation_date",
        string="Cycle Created On",
        store=False,
    )
    disbursement_cycle_ids = fields.One2many(
        "g2p.disbursement.cycle",
        "program_id",
        string="Disbursement Cycle",
    )
    latest_disbursement_cycle = fields.Char(
        string="Latest Disbursement Cycle",
        compute="_compute_latest_disbursement_cycle",
        store=False,
    )
    latest_disbursement_cycle_id = fields.Many2one(
        "g2p.disbursement.cycle",
        string="Latest Disbursement Cycle Record",
        compute="_compute_latest_disbursement_cycle_id",
        store=False,
    )
    latest_dc_cycle_name = fields.Char(
        related="latest_disbursement_cycle_id.cycle_name",
        string="Current Cycle",
        store=False,
    )
    latest_dc_version = fields.Char(
        related="latest_disbursement_cycle_id.current_list_id.mnemonic",
        string="Current Version",
        store=False,
    )
    latest_dc_stage = fields.Char(
        related="latest_disbursement_cycle_id.current_stage_display",
        string="Current Stage",
        store=False,
    )
    latest_dc_status = fields.Selection(
        related="latest_disbursement_cycle_id.current_approval_status",
        string="Current Status",
        store=False,
    )
    workflow_stage_ids = fields.One2many(
        "g2p.workflow.stage.definition",
        "program_id",
        string="Approval Workflow Stages",
    )
    enrollment_workflow_stage_ids = fields.One2many(
        "g2p.workflow.stage.definition",
        "program_id",
        string="Enrolment Workflow Stages",
        domain=[("cycle_type", "=", "ENROLMENT")],
    )
    disbursement_workflow_stage_ids = fields.One2many(
        "g2p.workflow.stage.definition",
        "program_id",
        string="Disbursement Workflow Stages",
        domain=[("cycle_type", "=", "DISBURSEMENT")],
    )
    service_providers_required = fields.Boolean(
        string="Service Providers required",
        default=True,
        help="If checked, the program will require benefits to be collected from specified agency and warehouse. If unchecked, beneficiaries may collect benefits from any agency/warehouse in the country. " \
    )
    verifications_for_enrolment = fields.Integer(
        string="Verifications required for enrolment",
        help="Minimum number of verifications required before lists can be approved"
    )
    auto_approve_enrolment = fields.Boolean(
        string="Auto approve enrollment",
        default=False,
        help="If enabled and the number of required verifications is 0, lists will be automatically approved as soon as they are created, without needing any verifications."
    )
    verifications_for_disbursement = fields.Integer(
        string="Verifications required for disbursement",
        help="Minimum number of verifications required before lists can be approved"

    )
    auto_approve_disbursement = fields.Boolean(
        string="Auto approve disbursement",
        default=False,
        help="If enabled and the number of required verifications is 0, lists will be automatically approved as soon as they are created, without needing any verifications."
    )
    # Cycle configuration
    enrollment_frequency = fields.Selection([
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Fortnightly', 'Fortnightly'),
        ('Monthly', 'Monthly'),
        ('BiMonthly', 'BiMonthly'),
        ('Quarterly', 'Quarterly'),
        ('SemiAnnually', 'SemiAnnually'),
        ('Annually', 'Annually'),
        ('OnDemand', 'OnDemand'),
    ], string="Enrollment Frequency", required=True, default='OnDemand')
    disbursement_frequency = fields.Selection([
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Fortnightly', 'Fortnightly'),
        ('Monthly', 'Monthly'),
        ('BiMonthly', 'BiMonthly'),
        ('Quarterly', 'Quarterly'),
        ('SemiAnnually', 'SemiAnnually'),
        ('Annually', 'Annually'),
        ('OnDemand', 'OnDemand'),
    ], string="Disbursement Frequency", required=True, default='OnDemand')

    on_demand_cycle_allowed = fields.Boolean(string="On-Demand Cycle Allowed")

    beneficiary_list = fields.Selection([
        ('latest_always', 'Latest Always'),
        ('labeled', 'Labeled')
    ], string="Beneficiary List", required=True, default='latest_always')

    label_for_beneficiary_list_id = fields.Many2one(
        'g2p.beneficiary.list', 
        string="Label for Beneficiary List"
    )
    show_label_for_beneficiary_list = fields.Boolean(compute='_compute_visibility_beneficiary', store=True)

    _sql_constraints = [
        (
            "unique_program_mnemonic",
            "unique(program_mnemonic)",
            "The program mnemonic must be unique!",
        )
    ]

    @api.depends('program_benefit_code_ids.benefit_code_id')
    def _compute_benefit_code_ids(self):
        for rec in self:
            rec.benefit_code_ids = rec.program_benefit_code_ids.mapped('benefit_code_id')

    @api.depends('beneficiary_list')
    def _compute_visibility_beneficiary(self):
        for rec in self:
            rec.show_label_for_beneficiary_list = rec.beneficiary_list == 'labeled'

    @api.depends('enrollment_cycle_ids.cycle_number')
    def _compute_latest_enrollment_cycle(self):
        for rec in self:
            latest = rec.enrollment_cycle_ids.sorted('cycle_number', reverse=True)[:1]
            rec.latest_enrollment_cycle = latest.cycle_name if latest else ''

    @api.depends('enrollment_cycle_ids.cycle_number')
    def _compute_latest_enrollment_cycle_id(self):
        for rec in self:
            latest = rec.enrollment_cycle_ids.sorted('cycle_number', reverse=True)[:1]
            rec.latest_enrollment_cycle_id = latest or False

    @api.depends('disbursement_cycle_ids.cycle_number')
    def _compute_latest_disbursement_cycle(self):
        for rec in self:
            latest = rec.disbursement_cycle_ids.sorted('cycle_number', reverse=True)[:1]
            rec.latest_disbursement_cycle = latest.cycle_name if latest else ''

    @api.depends('disbursement_cycle_ids.cycle_number')
    def _compute_latest_disbursement_cycle_id(self):
        for rec in self:
            latest = rec.disbursement_cycle_ids.sorted('cycle_number', reverse=True)[:1]
            rec.latest_disbursement_cycle_id = latest or False

    @api.depends('entitlement_id')
    def _compute_entitlement_inline_ids(self):
        for rec in self:
            rec.entitlement_inline_ids = rec.entitlement_id or False

    def action_open_edit(self):
        self.ensure_one()
        view_mode = self.env.context.get('program_view_mode', 'config')
        if view_mode == 'management':
            view_id = self.env.ref('g2p_pbms.view_g2p_programs_management_form').id
        else:
            view_id = self.env.ref('g2p_pbms.view_g2p_programs_config_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'g2p.program.definition',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'context': {
                'create': False,
                'program_form_edit': True,
                'program_form_create': False,
                'program_view_mode': view_mode,
            },
        }

    def action_view_enrollment_cycles(self):
        self.ensure_one()
        latest_cycle = self.env['g2p.enrollment.cycle'].search(
            [('program_id', '=', self.id)],
            order='cycle_number desc',
            limit=1,
        )
        if latest_cycle:
            return latest_cycle.action_open_view()
        # No cycles yet — fall back to cycle list so the user can create one
        return {
            'type': 'ir.actions.act_window',
            'name': '%s - Enrolment Cycles' % self.program_mnemonic,
            'res_model': 'g2p.enrollment.cycle',
            'view_mode': 'tree,form',
            'domain': [('program_id', '=', self.id)],
            'context': {
                'default_program_id': self.id,
                'create': True,
            },
            'target': 'current',
        }

    def action_open_create_cycle_wizard(self):
        """Open the Create New Cycle wizard from the program list, with program pre-filled."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Enrolment Cycle',
            'res_model': 'g2p.enrollment.cycle.create.wizard',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_program_id': self.id,
            },
        }


    def action_view_disbursement_cycles(self):
        self.ensure_one()
        latest_cycle = self.env['g2p.disbursement.cycle'].search(
            [('program_id', '=', self.id)],
            order='cycle_number desc',
            limit=1,
        )
        if latest_cycle:
            return latest_cycle.action_open_view()
        # No cycles yet — fall back to cycle list
        return {
            'type': 'ir.actions.act_window',
            'name': '%s - Disbursement Cycles' % self.program_mnemonic,
            'res_model': 'g2p.disbursement.cycle',
            'view_mode': 'tree,form',
            'domain': [('program_id', '=', self.id)],
            'context': {'default_program_id': self.id},
            'target': 'current',
        }

    def action_open_create_disbursement_cycle_wizard(self):
        """Open the Create New Disbursement Cycle wizard from the program list, with program pre-filled."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Disbursement Cycle',
            'res_model': 'g2p.disbursement.cycle.create.wizard',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {
                'default_program_id': self.id,
            },
        }
