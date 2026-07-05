from odoo import models, fields


class ApprovalReasonWizard(models.TransientModel):
    _name = "g2p.approval.reason.wizard"
    _description = "Approval Reason Wizard"

    pending_stage_id = fields.Many2one(
        "g2p.workflow.pending.stage",
        required=True,
        string="Pending Stage",
    )
    action_type = fields.Selection(
        [("approve", "Approve"), ("reject", "Reject")],
        required=True,
        string="Action",
    )
    reason = fields.Text(string="Reason")

    def action_confirm(self):
        self.ensure_one()
        pending = self.pending_stage_id
        if self.action_type == "approve":
            pending.list_id.action_approve_stage(reason=self.reason)
        else:
            pending.list_id.action_reject_stage(reason=self.reason)
        # Switch to approval history tab
        return {
            "type": "ir.actions.client",
            "tag": "g2p_approvals_tabbed",
            "params": {"default_tab": "history"},
        }
