# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Survey",
    "category": "G2P",
    "version": "17.0.1.0.0",
    "sequence": 5,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "mail",
        "survey",
        "g2p_registry_base",
        # g2p_registry defines _hide_unwanted_menus (which archives the Survey
        # app menu). Depend on it so our override in models/ir_module.py chains
        # correctly and re-enables survey.menu_surveys.
        "g2p_registry",
    ],
    "external_dependencies": {
        "python": ["requests", "xlsxwriter"],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/g2p_survey_views.xml",
        "views/g2p_survey_templates.xml",
        "views/menu.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
