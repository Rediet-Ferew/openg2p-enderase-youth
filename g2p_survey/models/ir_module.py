# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from odoo import models


class IrModule(models.Model):
    _inherit = "ir.module.module"

    def _hide_unwanted_menus(self):
        # g2p_registry force-archives a hardcoded list of non-G2P app menus
        # (survey.menu_surveys among them) on every module install/upgrade.
        # Enderase surfaces the native Survey app on purpose, so re-activate it
        # after g2p_registry hides it.
        res = super()._hide_unwanted_menus()
        menu = self.env.ref("survey.menu_surveys", raise_if_not_found=False)
        if menu and not menu.active:
            menu.sudo().write({"active": True})
        return res
