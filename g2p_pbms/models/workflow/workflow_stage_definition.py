from odoo import models, fields, api


class G2PWorkflowStageDefinition(models.Model):
    _name = "g2p.workflow.stage.definition"
    _description = "G2P Workflow Stage Definition"
    _order = "cycle_type, stage_number"

    program_id = fields.Many2one(
        "g2p.program.definition", required=True, index=True, ondelete="cascade"
    )
    cycle_type = fields.Selection(
        [("ENROLMENT", "Enrolment"), ("DISBURSEMENT", "Disbursement")],
        required=True,
        string="Cycle Type",
    )
    stage_number = fields.Integer(required=True, string="Stage Number")
    stage_name = fields.Char(required=True, string="Stage Name")
    group_id = fields.Many2one(
        "res.groups",
        string="Approval Group",
        required=True,
        help="The security group whose members can approve this stage.",
    )
    # is_final_stage = fields.Boolean(
    #     compute="_compute_is_final_stage", store=True, string="Is Final Stage"
    # )

    _sql_constraints = [
        (
            "unique_program_cycle_stage",
            "UNIQUE(program_id, cycle_type, stage_number)",
            "Stage number must be unique per program and cycle type.",
        ),
        (
            "unique_program_cycle_stage_name",
            "UNIQUE(program_id, cycle_type, stage_name)",
            "Stage name must be unique per program and cycle type.",
        ),
    ]

    # @api.depends("stage_number", "program_id", "cycle_type")
    # def _compute_is_final_stage(self):
    #     for rec in self:
    #         if not rec.program_id or not rec.cycle_type:
    #             rec.is_final_stage = False
    #             continue
    #         max_stage = self.search(
    #             [
    #                 ("program_id", "=", rec.program_id.id),
    #                 ("cycle_type", "=", rec.cycle_type),
    #             ],
    #             order="stage_number desc",
    #             limit=1,
    #         )
    #         rec.is_final_stage = max_stage.id == rec.id
