from odoo import models, fields, api


class EnrollmentCycleCreateWizard(models.TransientModel):
    _name = "g2p.enrollment.cycle.create.wizard"
    _description = "Create Enrollment Cycle Wizard"

    program_id = fields.Many2one(
        "g2p.program.definition",
        string="Program",
        required=True,
    )
    cycle_number = fields.Integer(
        string="Cycle Number",
        readonly=True,
        compute="_compute_cycle_number",
        store=False,
    )
    cycle_name = fields.Char(
        string="Cycle Name",
        required=True,
    )
    creation_date = fields.Datetime(
        string="Creation Date",
        default=fields.Datetime.now,
        readonly=True,
    )

    @api.depends("program_id")
    def _compute_cycle_number(self):
        for rec in self:
            if rec.program_id:
                last = self.env["g2p.enrollment.cycle"].search(
                    [("program_id", "=", rec.program_id.id)],
                    order="cycle_number desc",
                    limit=1,
                )
                rec.cycle_number = (last.cycle_number or 0) + 1
            else:
                rec.cycle_number = 1

    @api.onchange("program_id")
    def _onchange_program_id(self):
        if self.program_id:
            last = self.env["g2p.enrollment.cycle"].search(
                [("program_id", "=", self.program_id.id)],
                order="cycle_number desc",
                limit=1,
            )
            next_number = (last.cycle_number or 0) + 1
            self.cycle_name = "Cycle %s" % next_number

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        program_id = res.get("program_id") or self.env.context.get("default_program_id")
        if program_id:
            res["program_id"] = program_id
            last = self.env["g2p.enrollment.cycle"].search(
                [("program_id", "=", program_id)],
                order="cycle_number desc",
                limit=1,
            )
            next_number = (last.cycle_number or 0) + 1
            res["cycle_name"] = "Cycle %s" % next_number
        return res

    def action_confirm(self):
        self.ensure_one()
        cycle = self.env["g2p.enrollment.cycle"].create({
            "program_id": self.program_id.id,
            "cycle_name": self.cycle_name,
        })
        return cycle.action_open_view()
