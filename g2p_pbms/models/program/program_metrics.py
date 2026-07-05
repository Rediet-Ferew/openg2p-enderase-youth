from odoo import models, fields, api


class G2PProgramMetrics(models.Model):
    _name = "g2p.program.metrics"
    _description = "G2P Program Metrics"
    _rec_name = "program_id"

    program_id = fields.Many2one(
        "g2p.program.definition",
        string="Program",
        required=True,
        ondelete="cascade",
        index=True,
    )
    enrolment_cycle_count = fields.Integer(
        string="Enrolment Cycle Count",
        compute="_compute_cycle_counts",
        store=True,
    )
    disbursement_cycle_count = fields.Integer(
        string="Disbursement Cycle Count",
        compute="_compute_cycle_counts",
        store=True,
    )

    _sql_constraints = [
        (
            "unique_program_id",
            "unique(program_id)",
            "Only one metrics record per program is allowed.",
        ),
    ]

    @api.depends("program_id.enrollment_cycle_ids", "program_id.disbursement_cycle_ids")
    def _compute_cycle_counts(self):
        for rec in self:
            rec.enrolment_cycle_count = len(rec.program_id.enrollment_cycle_ids) if rec.program_id else 0
            rec.disbursement_cycle_count = len(rec.program_id.disbursement_cycle_ids) if rec.program_id else 0
