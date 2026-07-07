/** @odoo-module **/

import {Component} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import {WebClient} from "@web/webclient/webclient";
import {
    HOME_MENU_ACTION_TAG,
    ENDERASE_LOGO_URL,
    getAppHref,
    groupApps,
    normalizeIconData,
} from "../js/utils";

export class EnderaseSidebar extends Component {
    static template = "enderase_theme.Sidebar";

    setup() {
        this.actionService = useService("action");
        this.menuService = useService("menu");

        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.render());
        useBus(this.env.bus, "ROUTE_CHANGE", () => this.render());
    }

    get navGroups() {
        return groupApps(this.menuService.getApps());
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    get logoUrl() {
        return ENDERASE_LOGO_URL;
    }

    getAppHref(app) {
        return getAppHref(app);
    }

    getAppIcon(app) {
        return normalizeIconData(app);
    }

    isCurrentApp(app) {
        return this.currentApp?.id === app.id;
    }

    async openHomeMenu() {
        await this.actionService.doAction(HOME_MENU_ACTION_TAG, {clearBreadcrumbs: true});
    }

    async openApp(app) {
        await this.menuService.selectMenu(app);
    }
}

WebClient.components = {
    ...WebClient.components,
    EnderaseSidebar,
};
