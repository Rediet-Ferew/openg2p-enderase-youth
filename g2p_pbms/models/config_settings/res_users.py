from odoo import models, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        # Get HLG and LLG xmlids
        hlg_xmlids = [
            'g2p_pbms.group_program_super_administration',
            'g2p_pbms.group_program_administration',
            'g2p_pbms.group_enrolment_operation',
            'g2p_pbms.group_enrolment_verification',
            'g2p_pbms.group_enrolment_approval',
            'g2p_pbms.group_disbursement_operation',
            'g2p_pbms.group_disbursement_verification',
            'g2p_pbms.group_disbursement_approval',
            'g2p_pbms.group_geography_operation',
            'g2p_pbms.group_service_provider_operation',
            'g2p_pbms.group_audit_operation',
            'g2p_pbms.group_enrolment_1',
            'g2p_pbms.group_enrolment_2',
            'g2p_pbms.group_disbursement_1',
            'g2p_pbms.group_disbursement_2',
        ]
        llg_xmlids = [
            'g2p_pbms.group_abstract_model_viewer',
            'g2p_pbms.group_agency_viewer',
            'g2p_pbms.group_agency_editor',
            'g2p_pbms.group_benefit_code_viewer',
            'g2p_pbms.group_benefit_code_editor',
            'g2p_pbms.group_program_viewer',
            'g2p_pbms.group_program_editor',
            'g2p_pbms.group_warehouse_viewer',
            'g2p_pbms.group_warehouse_editor',
            'g2p_pbms.group_geography_viewer',
            'g2p_pbms.group_geography_editor',
            'g2p_pbms.group_beneficiary_list_viewer',
            'g2p_pbms.group_beneficiary_list_editor',
            'g2p_pbms.group_beneficiary_list_verifier',
            'g2p_pbms.group_enrolment_viewer',
            'g2p_pbms.group_enrolment_editor',
            'g2p_pbms.group_enrolment_approver',
            'g2p_pbms.group_disbursement_viewer',
            'g2p_pbms.group_disbursement_editor',
            'g2p_pbms.group_disbursement_approver',
            'g2p_pbms.group_priority_rules_viewer',
            'g2p_pbms.group_priority_rules_editor',
        ]
        # Map xmlids to group ids using env.ref
        hlg_ids = set()
        for xmlid in hlg_xmlids:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                hlg_ids.add(group.id)
        llg_ids = set()
        for xmlid in llg_xmlids:
            group = self.env.ref(xmlid, raise_if_not_found=False)
            if group:
                llg_ids.add(group.id)

        res = super().write(vals)
        for user in self:
            # Find HLGs the user is in
            high_groups = user.groups_id.filtered(lambda g: g.id in hlg_ids)
            # Collect all implied LLGs from HLGs
            implied = set()
            for g in high_groups:
                implied |= set(g.implied_ids.ids)
            # Remove any LLGs not covered by current HLGs
            for llg in user.groups_id:
                if llg.id in llg_ids and llg.id not in implied:
                    user.groups_id = [(3, llg.id)]
        return res
