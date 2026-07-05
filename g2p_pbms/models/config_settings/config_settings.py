from odoo import fields, models, api
from urllib.parse import urlparse


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    g2p_pbms_staff_portal_api_url = fields.Char(string="G2P Staff Portal API URL", config_parameter="g2p_pbms.staff_portal_api_url")
    g2p_bridge_api_url = fields.Char(string="G2P Bridge Partner API URL", config_parameter="g2p_pbms.g2p_bridge_api_url")

    g2p_document_store = fields.Many2one(
        "storage.backend",
        string="G2P Documents Store",
        config_parameter="g2p_pbms.document_store",
    )

    # Toggle fields
    keymanager_toggle = fields.Boolean(
        "Keymanager Active?",
        default=False,
        config_parameter="g2p_pbms.keymanager_toggle"
    )
    keycloak_toggle = fields.Boolean(
        "Keycloak Auth Active? (for Keymanager)",
        default=False,
        config_parameter="g2p_pbms.keycloak_toggle"
    )

    # Keymanager configs
    keymanager_api_base_url = fields.Char(
        "Keymanager API Base URL",
        config_parameter="g2p_pbms.keymanager_api_base_url"
    )
    keymanager_api_timeout = fields.Integer(
        "Keymanager API Timeout",
        default=10,
        config_parameter="g2p_pbms.keymanager_api_timeout"
    )
    keymanager_sign_application_id = fields.Char(
        "Keymanager Sign Application ID",
        default="PBMS",
        config_parameter="g2p_pbms.keymanager_sign_application_id"
    )
    keymanager_sign_reference_id = fields.Char(
        "Keymanager Sign Reference ID",
        default="",
        config_parameter="g2p_pbms.keymanager_sign_reference_id"
    )

    keymanager_access_token = fields.Char(
        config_parameter="g2p_pbms.keymanager_access_token"
    )
    keymanager_access_token_expiry = fields.Datetime(
        config_parameter="g2p_pbms.keymanager_access_token_expiry"
    )

    # Keycloak config
    keycloak_auth_url = fields.Char(
        "Keycloak Auth URL",
        config_parameter="g2p_pbms.keycloak_auth_url"
    )
    keycloak_auth_client_id = fields.Char(
        "Keycloak Auth Client ID",
        config_parameter="g2p_pbms.keycloak_auth_client_id"
    )
    keycloak_auth_client_secret = fields.Char(
        "Keycloak Auth Client Secret",
        config_parameter="g2p_pbms.keycloak_auth_client_secret"
    )
    keycloak_auth_grant_type = fields.Char(
        "Keycloak Auth Grant Type",
        config_parameter="g2p_pbms.keycloak_auth_grant_type"
    )