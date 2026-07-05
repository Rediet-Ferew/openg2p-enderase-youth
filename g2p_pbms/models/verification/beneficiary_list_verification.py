import hashlib
import uuid
from odoo import fields, models, api
import base64

import logging

_logger = logging.getLogger(__name__)


class G2PBeneficiaryListVerification(models.Model):
    _inherit = "storage.file"
    
    _sql_constraints = [
        ('unique_user_beneficiary_list_verification', 'UNIQUE(verified_by, beneficiary_list_id)', 
         'A user can only verify the same beneficiary list once!')
    ]

    name = fields.Char(
        string="File Name",
        default=lambda self: str(uuid.uuid4()),
        required=False
    )
    verified_by = fields.Many2one(
        'res.users',
        string="Verified by",
        required=True,
        default=lambda self: self.env.user
    )
    comment = fields.Text(string="Comment", required=True)
    verification_timestamp = fields.Datetime(
        string="Verification Timestamp", default=fields.Datetime.now, readonly=True
    )
    beneficiary_list_id = fields.Many2one(
        "g2p.beneficiary.list", string="Beneficiary List", index=True, required=True
    )

    @api.model
    def default_get(self, fields_list):
        res = super(G2PBeneficiaryListVerification, self).default_get(fields_list)
        if 'backend_id' in fields_list and not res.get('backend_id'):
            doc_store_id_str = (
                self.env["ir.config_parameter"].sudo().get_param("g2p_pbms.document_store")
            )
            if doc_store_id_str:
                res['backend_id'] = int(doc_store_id_str)
        return res
    
    def _prepare_meta_for_file(self):
        """Safely prepare metadata only if a file is present."""
        if not self.data:
            return {}
        bin_data = base64.b64decode(self.data)
        checksum = hashlib.sha1(bin_data).hexdigest()
        relative_path = self._build_relative_path(checksum)
        return {
            "checksum": checksum,
            "file_size": len(bin_data),
            "relative_path": relative_path,
        }

    def _inverse_data(self):
        """Push data to backend only if file content exists."""
        for record in self:
            if not record.data:
                continue
            record.write(record._prepare_meta_for_file())
            record.backend_id.sudo().add(
                record.relative_path,
                record.data,
                mimetype=record.mimetype,
                binary=False,
            )
