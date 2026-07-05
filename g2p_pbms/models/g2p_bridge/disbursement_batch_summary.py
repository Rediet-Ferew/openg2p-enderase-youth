from odoo import models, fields, api


class DisbursementBatchSummaryWizard(models.TransientModel):
    _name = 'g2p.disbursement.batch.summary.wizard'
    _description = 'Disbursement Batch Summary Wizard'

    wizard_id = fields.Many2one(
        'g2p.bgtask.summary.wizard',
        string='BG Task Summary Wizard',
        required=False,
    )
    disbursement_batch_control_id = fields.Char(string='Disbursement Batch Control ID', required=True)
    disbursement_cycle_id = fields.Integer(string='Disbursement Cycle ID', required=False)
    disbursement_cycle_code_mnemonic = fields.Char(string='Disbursement Cycle Code Mnemonic', required=False)
    disbursement_envelope_id = fields.Char(string='Disbursement Envelope ID', required=True)

    # Benefit code
    benefit_code_id = fields.Integer(string='Benefit Code ID', required=False)
    benefit_code_mnemonic = fields.Char(string='Benefit Code Mnemonic', required=False)
    benefit_type = fields.Char(string='Benefit Type', required=True)
    measurement_unit = fields.Char(string='Measurement Unit', required=True)

    # FA Resolution
    fa_resolution_status = fields.Char(string='FA Resolution Status', required=False)
    fa_resolution_timestamp = fields.Datetime(string='FA Resolution Timestamp', required=False)
    fa_resolution_latest_error_code = fields.Char(string='FA Resolution Latest Error Code', required=False)
    fa_resolution_attempts = fields.Integer(string='FA Resolution Attempts', required=False)

    # Sponsor Bank Dispatch
    sponsor_bank_dispatch_status = fields.Char(string='Sponsor Bank Dispatch Status', required=False)
    sponsor_bank_dispatch_timestamp = fields.Datetime(string='Sponsor Bank Dispatch Timestamp', required=False)
    sponsor_bank_dispatch_latest_error_code = fields.Char(string='Sponsor Bank Dispatch Latest Error Code', required=False)
    sponsor_bank_dispatch_attempts = fields.Integer(string='Sponsor Bank Dispatch Attempts', required=False)

    # Geo Resolution
    geo_resolution_status = fields.Char(string='Geo Resolution Status', required=False)
    geo_resolution_timestamp = fields.Datetime(string='Geo Resolution Timestamp', required=False)
    geo_resolution_latest_error_code = fields.Char(string='Geo Resolution Latest Error Code', required=False)
    geo_resolution_attempts = fields.Integer(string='Geo Resolution Attempts', required=False)

    # Warehouse Allocation
    warehouse_allocation_status = fields.Char(string='Warehouse Allocation Status', required=False)
    warehouse_allocation_timestamp = fields.Datetime(string='Warehouse Allocation Timestamp', required=False)
    warehouse_allocation_latest_error_code = fields.Char(string='Warehouse Allocation Latest Error Code', required=False)
    warehouse_allocation_attempts = fields.Integer(string='Warehouse Allocation Attempts', required=False)

    # Agency Allocation
    agency_allocation_status = fields.Char(string='Agency Allocation Status', required=False)
    agency_allocation_timestamp = fields.Datetime(string='Agency Allocation Timestamp', required=False)
    agency_allocation_latest_error_code = fields.Char(string='Agency Allocation Latest Error Code', required=False)
    agency_allocation_attempts = fields.Integer(string='Agency Allocation Attempts', required=False)

    # Related Geos (One2many to a new model for DisbursementBatchControlGeo)
    disbursement_batch_summary_geo_ids = fields.One2many(
        'g2p.disbursement.batch.summary.geo',
        'disbursement_batch_summary_id',
        string='Disbursement Batch Control Geos'
    )

    @api.depends('benefit_code_id')
    def _compute_benefit_type(self):
        for rec in self:
            benefit_type = False
            if rec.benefit_code_id:
                benefit_code = self.env['g2p.benefit.codes'].search([('id', '=', rec.benefit_code_id)], limit=1)
                benefit_type = benefit_code.benefit_type if benefit_code else False
            rec.benefit_type = benefit_type

class DisbursementBatchSummaryGeo(models.TransientModel):
    _name = 'g2p.disbursement.batch.summary.geo'
    _description = 'Disbursement Batch Summary Geo'

    disbursement_batch_summary_id = fields.Many2one(
        'g2p.disbursement.batch.summary.wizard',
        string='Disbursement Batch Summary',
        required=False,
        ondelete='cascade'
    )

    disbursement_batch_control_geo_id = fields.Char(string='Disbursement Batch Control Geo ID', required=False)
    disbursement_cycle_id = fields.Char(string='Disbursement Cycle ID')
    disbursement_envelope_id = fields.Char(string='Disbursement Envelope ID')
    disbursement_batch_control_id = fields.Char(string='Disbursement Batch Control ID')

    administrative_zone_id_large = fields.Char(string='Large Zone ID')
    administrative_zone_mnemonic_large = fields.Char(string='Large Zone Mnemonic')
    administrative_zone_id_small = fields.Char(string='Small Zone ID')
    administrative_zone_mnemonic_small = fields.Char(string='Small Zone Mnemonic')

    no_of_beneficiaries = fields.Integer(string='No. of Beneficiaries')
    total_quantity = fields.Float(string='Total Quantity')

    # Warehouse
    warehouse_id = fields.Char(string='Warehouse ID')
    warehouse_mnemonic = fields.Char(string='Warehouse Mnemonic')
    warehouse_additional_attributes = fields.Char(string='Warehouse Attributes')

    # Agency
    agency_id = fields.Char(string='Agency ID')
    agency_mnemonic = fields.Char(string='Agency Mnemonic')
    agency_additional_attributes = fields.Char(string='Agency Attributes')

    # Notification status
    warehouse_notification_status = fields.Char(string='Warehouse Notification Status')
    agency_notification_status = fields.Char(string='Agency Notification Status')

