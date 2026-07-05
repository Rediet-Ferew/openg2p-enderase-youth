from odoo import models, api
import base64
import json
import logging
from datetime import datetime

import requests
from jose import jwt

_logger = logging.getLogger(__name__)


class KeymanagerProvider(models.AbstractModel):
    _name = 'keymanager.provider'
    _description = 'Keymanager Provider'

    @api.model
    def km_generate_current_time(self):
        return f'{datetime.now().isoformat(timespec = "milliseconds")}Z'

    def jwt_sign_keymanager(
        self,
        data,
        include_payload=True,
        include_certificate=False,
        include_cert_hash=False,
        **kwargs,
    ) -> str:
        keymanager_toggle = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_toggle')
        if not keymanager_toggle:
            return None

        keycloak_toggle = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keycloak_toggle')
        keymanager_api_base_url = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_api_base_url')
        keymanager_sign_application_id = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_sign_application_id')
        keymanager_sign_reference_id = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_sign_reference_id')

        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        
        access_token: str = None
        if keycloak_toggle:
            access_token = self.km_get_access_token()
            
        current_time = self.km_generate_current_time()
        url = f"{keymanager_api_base_url}/jwtSign"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "dataToSign": self.km_urlsafe_b64encode(data),
                "applicationId": keymanager_sign_application_id or "",
                "referenceId": keymanager_sign_reference_id or "",
                "includePayload": include_payload,
                "includeCertificate": include_certificate,
                "includeCertHash": include_cert_hash,
            },
        }
        response = requests.post(url, json=payload, headers=headers)
        _logger.debug("Keymanager JWT Sign API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response", {})
        if response:
            return response.get("jwtSignedData")
        raise ValueError("Could not sign jwt, invalid keymanager response")

    def jwt_verify_keymanager(self, data: str, **kwargs):
        keymanager_toggle = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_toggle')
        if not keymanager_toggle:
            return None

        keymanager_api_base_url = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_api_base_url')
        keymanager_sign_application_id = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_sign_application_id')
        keymanager_sign_reference_id = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_sign_reference_id')

        access_token = self.km_get_access_token()
        current_time = self.km_generate_current_time()
        url = f"{keymanager_api_base_url}/jwtVerify"
        headers = {"Cookie": f"Authorization={access_token}"}
        payload = {
            "id": "string",
            "version": "string",
            "requesttime": current_time,
            "metadata": {},
            "request": {
                "jwtSignatureData": data,
                "applicationId": keymanager_sign_application_id or "",
                "referenceId": keymanager_sign_reference_id or "",
                "validateTrust": False,
            },
        }
        response = requests.post(url, json=payload, headers=headers)
        _logger.debug("Keymanager JWT Verify API response: %s", response.text)
        response.raise_for_status()
        if response:
            response = response.json()
        if response:
            response = response.get("response", {})
        if response:
            response = response.get("signatureValid", False)
        else:
            raise ValueError("Could not verify jwt, invalid keymanager response")
        if response:
            return jwt.get_unverified_claims(data)
        raise ValueError("invalid jwt signature")

    def km_get_access_token(self):
        keymanager_access_token = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_access_token')
        keymanager_access_token_expiry = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keymanager_access_token_expiry')
        
        keycloak_auth_url = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keycloak_auth_url')
        keycloak_auth_client_id = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keycloak_auth_client_id')
        keycloak_auth_client_secret = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keycloak_auth_client_secret')
        keycloak_auth_grant_type = self.env['ir.config_parameter'].sudo().get_param('g2p_pbms.keycloak_auth_grant_type')

        if (
            keymanager_access_token
            and keymanager_access_token_expiry
            and keymanager_access_token_expiry > datetime.now()
        ):
            return keymanager_access_token
        data = {
            "client_id": keycloak_auth_client_id,
            "client_secret": keycloak_auth_client_secret,
            "grant_type": keycloak_auth_grant_type,
        }
        response = requests.post(keycloak_auth_url, data=data)
        _logger.debug("Keymanager get Certificates API response: %s", response.text)
        response.raise_for_status()
        access_token = response.json().get("access_token", None)
        token_exp = jwt.get_unverified_claims(access_token).get("exp")
        self.write(
            {
                "keymanager_access_token": access_token,
                "keymanager_access_token_expiry": datetime.fromtimestamp(token_exp)
                if isinstance(token_exp, int)
                else datetime.fromisoformat(token_exp)
                if isinstance(token_exp, str)
                else token_exp,
            }
        )
        return access_token

    @api.model
    def km_urlsafe_b64encode(self, input_data: bytes) -> str:
        return base64.urlsafe_b64encode(input_data).decode().rstrip("=")

    @api.model
    def km_urlsafe_b64decode(self, input_data: str) -> bytes:
        return base64.urlsafe_b64decode(input_data.encode() + b"=" * (-len(input_data) % 4))