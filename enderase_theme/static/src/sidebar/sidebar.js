/** @odoo-module **/

import {Component, onMounted, onWillUnmount, useState} from "@odoo/owl";
import {useBus, useService} from "@web/core/utils/hooks";
import {WebClient} from "@web/webclient/webclient";

const HOME_MENU_ACTION_TAG = "enderase_theme.home_menu";
const ENDERASE_LOGO_URL = "/enderase_theme/static/src/img/enderase-icon.png";
const SIDEBAR_COLLAPSED_WIDTH = "84px";
const SIDEBAR_EXPANDED_WIDTH = "264px";
const SIDEBAR_STORAGE_KEY = "enderase_theme.sidebar_expanded";

function readStoredExpandedState() {
    try {
        return window.localStorage?.getItem(SIDEBAR_STORAGE_KEY) === "1";
    } catch {
        return false;
    }
}

function writeStoredExpandedState(isExpanded) {
    try {
        window.localStorage?.setItem(SIDEBAR_STORAGE_KEY, isExpanded ? "1" : "0");
    } catch {
        // Storage can be unavailable in private windows; the sidebar still works.
    }
}

function applySidebarWidth(isExpanded) {
    document.documentElement.style.setProperty(
        "--enderase-sidebar-width",
        isExpanded ? SIDEBAR_EXPANDED_WIDTH : SIDEBAR_COLLAPSED_WIDTH
    );
}

function normalizeIconData(app) {
    if (!app.webIconData) {
        return "/base/static/description/icon.png";
    }
    if (app.webIconData.startsWith("data:image")) {
        return app.webIconData;
    }
    const iconData = app.webIconData.replace(/\s/g, "");
    const prefix = iconData.startsWith("P")
        ? "data:image/svg+xml;base64,"
        : "data:image/png;base64,";
    return `${prefix}${iconData}`;
}

export class EnderaseSidebar extends Component {
    static template = "enderase_theme.Sidebar";

    setup() {
        this.actionService = useService("action");
        this.menuService = useService("menu");
        this.state = useState({
            expanded: readStoredExpandedState(),
        });

        onMounted(() => applySidebarWidth(this.state.expanded));
        onWillUnmount(() => {
            document.documentElement.style.removeProperty("--enderase-sidebar-width");
        });

        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.render());
        useBus(this.env.bus, "ROUTE_CHANGE", () => this.render());
    }

    get apps() {
        return this.menuService.getApps();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    get logoUrl() {
        return ENDERASE_LOGO_URL;
    }

    getAppHref(app) {
        const hrefParts = [`menu_id=${app.id}`];
        if (app.actionID) {
            hrefParts.push(`action=${app.actionID}`);
        }
        return `#${hrefParts.join("&")}`;
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

    toggleExpanded() {
        this.state.expanded = !this.state.expanded;
        writeStoredExpandedState(this.state.expanded);
        applySidebarWidth(this.state.expanded);
    }
}

WebClient.components = {
    ...WebClient.components,
    EnderaseSidebar,
};
