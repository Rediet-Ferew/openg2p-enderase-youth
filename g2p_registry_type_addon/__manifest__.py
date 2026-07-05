{
    "name": "Enderase PBMS Registry Type Addon",
    "version": "3.0.0",
    "summary": "Enderase registry types for OpenG2P PBMS",
    "description": "Registry type mappings used by PBMS for Enderase target registries.",
    "category": "OpenG2P",
    "license": "LGPL-3",
    "depends": ["base_setup", "web"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
