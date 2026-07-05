from odoo import models

class ResGroups(models.Model):
    _inherit = 'res.groups'

    def get_application_groups(self, domain=None):
        if domain is None:
            domain = []
        hidden_group_xml_ids = [
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
        hidden_group_ids = []
        for xml_id in hidden_group_xml_ids:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            if group:
                hidden_group_ids.append(group.id)
        if hidden_group_ids:
            domain.append(('id', 'not in', hidden_group_ids))
        return super().get_application_groups(domain=domain)
