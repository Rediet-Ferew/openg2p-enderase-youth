/** @odoo-module **/

import {Component, onMounted, onWillUnmount, useExternalListener, useState} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {WebClient} from "@web/webclient/webclient";
import {NavBar} from "@web/webclient/navbar/navbar";

const HOME_MENU_ACTION_TAG = "enderase_theme.home_menu";
const HOME_MENU_SYSTRAY_KEYS = ["mail.activity_menu", "mail.messaging_menu", "web.user_menu"];
const APP_OPEN_ANIMATION_MS = 180;
const ENDERASE_LOGO_URL = "/enderase_theme/static/src/img/enderase-icon.png";

function isHomeMenuOpen() {
    return document.body?.classList.contains("o_enderase_home_menu_open") || false;
}

function cleanHomeMenuRoute(router) {
    router.pushState(
        {
            action: HOME_MENU_ACTION_TAG,
            menu_id: undefined,
            model: undefined,
            view_type: undefined,
            id: undefined,
            active_id: undefined,
            active_ids: undefined,
        },
        {replace: true}
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

export class EnderaseHomeMenu extends Component {
    static template = "enderase_theme.HomeMenu";
    static props = ["*"];

    setup() {
        this.menuService = useService("menu");
        this.router = useService("router");
        this.state = useState({
            isLeaving: false,
            launchingAppId: null,
        });

        onMounted(() => {
            document.body.classList.add("o_enderase_home_menu_open");
            cleanHomeMenuRoute(this.router);
            this.env.bus.trigger("MENUS:APP-CHANGED");
        });
        onWillUnmount(() => {
            document.body.classList.remove("o_enderase_home_menu_open");
            this.env.bus.trigger("MENUS:APP-CHANGED");
        });
    }

    get apps() {
        return this.menuService.getApps();
    }

    get brandIcon() {
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

    async openApp(app) {
        if (this.state.isLeaving) {
            return;
        }
        this.state.isLeaving = true;
        this.state.launchingAppId = app.id;
        await new Promise((resolve) => setTimeout(resolve, APP_OPEN_ANIMATION_MS));
        await this.menuService.selectMenu(app);
    }
}

registry.category("actions").add(HOME_MENU_ACTION_TAG, EnderaseHomeMenu);

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        useExternalListener(window, "click", this.onEnderaseHomeMenuClick, {capture: true});
    },

    get currentApp() {
        if (isHomeMenuOpen()) {
            return;
        }
        return super.currentApp;
    },

    get systrayItems() {
        const items = super.systrayItems;
        if (!isHomeMenuOpen()) {
            return items;
        }
        return items
            .filter((item) => HOME_MENU_SYSTRAY_KEYS.includes(item.key))
            .sort(
                (left, right) =>
                    HOME_MENU_SYSTRAY_KEYS.indexOf(left.key) -
                    HOME_MENU_SYSTRAY_KEYS.indexOf(right.key)
            );
    },

    onEnderaseHomeMenuClick(ev) {
        const target = ev.target instanceof Element ? ev.target : null;
        const appsMenu = target?.closest(".o_navbar_apps_menu");
        const toggler = target?.closest(".dropdown-toggle");

        if (!appsMenu || !toggler) {
            return;
        }

        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation();
        this.actionService.doAction(HOME_MENU_ACTION_TAG, {clearBreadcrumbs: true});
        cleanHomeMenuRoute(this.env.services.router);
    },
});

patch(WebClient.prototype, {
    async loadRouterState() {
        const hash = this.router.current.hash;
        const hasExplicitState =
            hash.action || hash.menu_id || hash.model || hash.view_type || hash.id;

        if (hash.action === HOME_MENU_ACTION_TAG) {
            cleanHomeMenuRoute(this.router);
            await this.actionService.doAction(HOME_MENU_ACTION_TAG, {clearBreadcrumbs: true});
            return;
        }

        if (!hasExplicitState) {
            await this.actionService.doAction(HOME_MENU_ACTION_TAG, {clearBreadcrumbs: true});
            return;
        }

        await super.loadRouterState(...arguments);
    },

    async _loadDefaultApp() {
        await this.actionService.doAction(HOME_MENU_ACTION_TAG, {clearBreadcrumbs: true});
    },
});
