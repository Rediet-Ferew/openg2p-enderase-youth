# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

import requests
from urllib.parse import quote

from odoo.exceptions import UserError


class ODKCentralClient:
    def __init__(self, server):
        self.server = server
        self.base_url = (server.base_url or "").rstrip("/")
        self.timeout = server.timeout or 30
        self.verify_ssl = bool(server.verify_ssl)
        self._token = None

    def _url(self, path):
        if not self.base_url:
            raise UserError("Set the ODK Central URL before connecting.")
        return f"{self.base_url}/{path.lstrip('/')}"

    def _path_segment(self, value):
        return quote(str(value), safe="")

    def _login(self):
        response = requests.post(
            self._url("/v1/sessions"),
            json={
                "email": self.server.api_email,
                "password": self.server.api_password,
            },
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        self._raise_for_response(response)
        token = response.json().get("token")
        if not token:
            raise UserError("ODK Central did not return a session token.")
        self._token = token

    def _headers(self, headers=None):
        if not self._token:
            self._login()
        result = {"Authorization": f"Bearer {self._token}"}
        if headers:
            result.update(headers)
        return result

    def _raise_for_response(self, response, expected=(200,)):
        if response.status_code in expected:
            return
        try:
            payload = response.json()
            message = payload.get("message") or payload
        except ValueError:
            message = response.text
        raise UserError(
            "ODK Central request failed (%s): %s"
            % (response.status_code, message or response.reason)
        )

    def request(self, method, path, expected=(200,), **kwargs):
        headers = kwargs.pop("headers", {})
        response = requests.request(
            method,
            self._url(path),
            headers=self._headers(headers),
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs,
        )
        self._raise_for_response(response, expected=expected)
        if response.status_code == 204 or not response.content:
            return {}
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def request_content(self, method, path, expected=(200,), **kwargs):
        """Like ``request`` but returns the raw response body and content type.

        Used for binary payloads such as ODK submission media attachments.
        """
        headers = kwargs.pop("headers", {})
        response = requests.request(
            method,
            self._url(path),
            headers=self._headers(headers),
            timeout=self.timeout,
            verify=self.verify_ssl,
            **kwargs,
        )
        self._raise_for_response(response, expected=expected)
        return response.content, response.headers.get("Content-Type", "application/octet-stream")

    def get_current_user(self):
        return self.request("GET", "/v1/users/current")

    # -- Projects ---------------------------------------------------------

    def list_projects(self):
        result = self.request("GET", "/v1/projects")
        return result if isinstance(result, list) else []

    def get_project(self, project_id):
        response = requests.get(
            self._url(f"/v1/projects/{project_id}"),
            headers=self._headers(),
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        if response.status_code == 404:
            return None
        self._raise_for_response(response)
        return response.json()

    def find_project_by_name(self, name):
        target = (name or "").strip().lower()
        for project in self.list_projects():
            if (project.get("name") or "").strip().lower() == target:
                return project
        return None

    def create_project(self, name):
        return self.request("POST", "/v1/projects", json={"name": name})

    def find_user_by_email(self, email):
        users = self.request("GET", "/v1/users", params={"q": email})
        for user in users:
            if (user.get("email") or "").lower() == (email or "").lower():
                return user
        return None

    def create_user(self, email, password=None, display_name=None):
        existing = self.find_user_by_email(email)
        if existing:
            actor_id = existing.get("id")
            if display_name and display_name != existing.get("displayName"):
                return self.request(
                    "PATCH",
                    f"/v1/users/{actor_id}",
                    json={"displayName": display_name, "email": email},
                )
            return existing

        payload = {"email": email}
        if password:
            payload["password"] = password
        user = self.request("POST", "/v1/users", json=payload)
        if display_name and user.get("id"):
            user = self.request(
                "PATCH",
                f"/v1/users/{user['id']}",
                json={"displayName": display_name, "email": email},
            )
        return user

    def create_app_user(self, project_id, display_name, properties=None):
        payload = {"displayName": display_name}
        if properties:
            payload["properties"] = properties
        return self.request("POST", f"/v1/projects/{project_id}/app-users", json=payload)

    def get_form(self, project_id, xml_form_id):
        form_id = self._path_segment(xml_form_id)
        response = requests.get(
            self._url(f"/v1/projects/{project_id}/forms/{form_id}"),
            headers=self._headers(),
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        if response.status_code == 404:
            return None
        self._raise_for_response(response)
        return response.json()

    def push_form_definition(
        self,
        project_id,
        xml_form_id,
        content,
        content_type,
        publish=True,
        form_id_fallback=None,
    ):
        """Create or update a form from a definition (XForm XML or XLSForm xlsx).

        ODK Central detects XLSForm uploads from the ``Content-Type`` and runs
        pyxform server-side, so the same endpoints handle both formats. ``content``
        must be ``bytes``.
        """
        headers = {"Content-Type": content_type}
        if form_id_fallback:
            # Central uses this as the xmlFormId when the definition itself does
            # not carry one (e.g. an XLSForm without a form_id in its settings).
            headers["X-XlsForm-FormId-Fallback"] = str(form_id_fallback)
        params = {"ignoreWarnings": "true"}
        existing = self.get_form(project_id, xml_form_id)
        form_id = self._path_segment(xml_form_id)
        if existing:
            self.request(
                "POST",
                f"/v1/projects/{project_id}/forms/{form_id}/draft",
                headers=headers,
                params=params,
                data=content,
            )
            if publish:
                self.request(
                    "POST",
                    f"/v1/projects/{project_id}/forms/{form_id}/draft/publish",
                )
            return self.get_form(project_id, xml_form_id)

        if publish:
            params["publish"] = "true"
        return self.request(
            "POST",
            f"/v1/projects/{project_id}/forms",
            headers=headers,
            params=params,
            data=content,
        )

    def push_form_xml(self, project_id, xml_form_id, xml_content, publish=True):
        return self.push_form_definition(
            project_id,
            xml_form_id,
            xml_content.encode("utf-8"),
            "application/xml",
            publish=publish,
        )

    def push_form_xlsx(self, project_id, xml_form_id, xlsx_content, publish=True):
        return self.push_form_definition(
            project_id,
            xml_form_id,
            xlsx_content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            publish=publish,
            form_id_fallback=xml_form_id,
        )

    def publish_form_draft(self, project_id, xml_form_id, version=None):
        form_id = self._path_segment(xml_form_id)
        params = {}
        if version:
            params["version"] = version
        self.request(
            "POST",
            f"/v1/projects/{project_id}/forms/{form_id}/draft/publish",
            params=params or None,
        )
        return self.get_form(project_id, xml_form_id)

    def assign_form_role(self, project_id, xml_form_id, role_id, actor_id):
        form_id = self._path_segment(xml_form_id)
        return self.request(
            "POST",
            f"/v1/projects/{project_id}/forms/{form_id}/assignments/{role_id}/{actor_id}",
        )

    def list_form_submissions(self, project_id, xml_form_id):
        form_id = self._path_segment(xml_form_id)
        return self.request(
            "GET",
            f"/v1/projects/{project_id}/forms/{form_id}/submissions",
            headers={"X-Extended-Metadata": "true"},
        )

    def get_submission_xml(self, project_id, xml_form_id, instance_id):
        form_id = self._path_segment(xml_form_id)
        instance = self._path_segment(instance_id)
        return self.request(
            "GET",
            f"/v1/projects/{project_id}/forms/{form_id}/submissions/{instance}.xml",
            headers={"Accept": "application/xml"},
        )

    # -- Submission media attachments -------------------------------------

    def list_submission_attachments(self, project_id, xml_form_id, instance_id):
        """Return the list of media attachments for a submission.

        Each item looks like ``{"name": "photo.jpg", "exists": True}``.
        """
        form_id = self._path_segment(xml_form_id)
        instance = self._path_segment(instance_id)
        result = self.request(
            "GET",
            f"/v1/projects/{project_id}/forms/{form_id}/submissions/{instance}/attachments",
        )
        return result if isinstance(result, list) else []

    def download_submission_attachment(self, project_id, xml_form_id, instance_id, filename):
        """Download a single submission media attachment as ``(bytes, content_type)``."""
        form_id = self._path_segment(xml_form_id)
        instance = self._path_segment(instance_id)
        name = self._path_segment(filename)
        return self.request_content(
            "GET",
            f"/v1/projects/{project_id}/forms/{form_id}/submissions/{instance}/attachments/{name}",
        )

    # -- Form media attachments (admin-provided) --------------------------

    # -- App user lifecycle -----------------------------------------------

    def revoke_app_user(self, project_id, actor_id):
        """Revoke an ODK Collect app user (its token stops working)."""
        return self.request(
            "DELETE",
            f"/v1/projects/{project_id}/app-users/{actor_id}",
            expected=(200, 204),
        )
