import logging
import requests
from odoo import models, fields, api
import datetime

_logger = logging.getLogger(__name__)

class DisbursementEnvelopeSummaryWizard(models.TransientModel):
    _name = 'g2p.disbursement.envelope.summary.wizard'
    _description = 'Disbursement Envelope Summary Wizard'
    
    wizard_id = fields.Many2one(
        'g2p.bgtask.summary.wizard',
        string='BG Task Summary Wizard',
        required=False,
    )
    disbursement_envelope_id = fields.Char(string='Disbursement Envelope ID', required=False)
    benefit_code_id = fields.Char(string='Benefit Code ID', required=False)
    benefit_code_mnemonic = fields.Char(string='Benefit Code Mnemonic', required=False)
    benefit_type = fields.Char(string='Benefit Type', required=False)
    measurement_unit = fields.Char(string='Measurement Unit')

    number_of_beneficiaries_received = fields.Integer(string='Number of Beneficiaries Received', required=False)
    number_of_beneficiaries_declared = fields.Integer(string='Number of Beneficiaries Declared', required=False)
    number_of_disbursements_declared = fields.Integer(string='Number of Disbursements Declared', required=False)
    number_of_disbursements_received = fields.Integer(string='Number of Disbursements Received', required=False)
    total_disbursement_quantity_declared = fields.Char(string='Total Disbursement Quantity Declared', required=False)
    total_disbursement_quantity_received = fields.Char(string='Total Disbursement Quantity Received', required=False)

    funds_available_with_bank = fields.Char(string='Funds Available With Bank', required=False)
    funds_available_latest_timestamp = fields.Datetime(string='Funds Available Latest Timestamp', required=False)
    funds_available_latest_error_code = fields.Char(string='Funds Available Latest Error Code', required=False)
    funds_available_attempts = fields.Integer(string='Funds Available Attempts', required=False)

    funds_blocked_with_bank = fields.Char(string='Funds Blocked With Bank', required=False)
    funds_blocked_latest_timestamp = fields.Datetime(string='Funds Blocked Latest Timestamp', required=False)
    funds_blocked_latest_error_code = fields.Char(string='Funds Blocked Latest Error Code', required=False)
    funds_blocked_attempts = fields.Integer(string='Funds Blocked Attempts', required=False)
    funds_blocked_reference_number = fields.Char(string='Funds Blocked Reference Number', required=False)

    number_of_disbursements_shipped = fields.Integer(string='Number of Disbursements Shipped', required=False)
    number_of_disbursements_reconciled = fields.Integer(string='Number of Disbursements Reconciled', required=False)
    number_of_disbursements_reversed = fields.Integer(string='Number of Disbursements Reversed', required=False)

    no_of_warehouses_allocated = fields.Integer(string='No. of Warehouses Allocated', required=False)
    no_of_warehouses_notified = fields.Integer(string='No. of Warehouses Notified', required=False)
    no_of_agencies_allocated = fields.Integer(string='No. of Agencies Allocated', required=False)
    no_of_agencies_notified = fields.Integer(string='No. of Agencies Notified', required=False)
    no_of_beneficiaries_notified = fields.Integer(string='No. of Beneficiaries Notified', required=False)
    no_of_pods_received = fields.Integer(string='No. of PODs Received', required=False)

    # Related Geos (One2many to a new model for DisbursementEnvelopeSummaryGeo)
    disbursement_envelope_summary_geo_ids = fields.One2many(
        'g2p.disbursement.envelope.summary.geo',
        'disbursement_envelope_summary_id',
        string='Disbursement Envelope Summary Geos'
    )


class DisbursementEnvelopeSummaryGeo(models.TransientModel):
    _name = 'g2p.disbursement.envelope.summary.geo'
    _description = 'Disbursement Envelope Summary Geo'

    disbursement_envelope_summary_id = fields.Many2one(
        'g2p.disbursement.envelope.summary.wizard',
        string='Disbursement Envelope Summary',
        required=False,
        ondelete='cascade'
    )

    disbursement_batch_control_geo_id = fields.Char(string='Disbursement Batch Control Geo ID', required=False)
    disbursement_cycle_id = fields.Char(string='Disbursement Cycle ID', required=False)
    disbursement_envelope_id = fields.Char(string='Disbursement Envelope ID', required=False)
    disbursement_batch_control_id = fields.Char(string='Disbursement Batch Control ID', required=False)
    administrative_zone_id_large = fields.Char(string='Large Zone ID', required=False)
    administrative_zone_mnemonic_large = fields.Char(string='Large Zone Mnemonic', required=False)
    administrative_zone_id_small = fields.Char(string='Small Zone ID', required=False)
    administrative_zone_mnemonic_small = fields.Char(string='Small Zone Mnemonic', required=False)
    no_of_beneficiaries = fields.Integer(string='No. of Beneficiaries', required=False)
    total_quantity = fields.Float(string='Total Quantity', required=False)
    warehouse_id = fields.Char(string='Warehouse ID', required=False)
    warehouse_mnemonic = fields.Char(string='Warehouse Mnemonic', required=False)
    warehouse_additional_attributes = fields.Char(string='Warehouse Attributes', required=False)
    agency_id = fields.Char(string='Agency ID', required=False)
    agency_mnemonic = fields.Char(string='Agency Mnemonic', required=False)
    agency_additional_attributes = fields.Char(string='Agency Attributes', required=False)
    warehouse_notification_status = fields.Char(string='Warehouse Notification Status', required=False)
    agency_notification_status = fields.Char(string='Agency Notification Status', required=False)