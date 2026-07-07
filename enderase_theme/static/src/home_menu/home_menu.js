/** @odoo-module **/

import {Component, onMounted, onWillUnmount, useExternalListener, useState} from "@odoo/owl";
import {Domain} from "@web/core/domain";
import {patch} from "@web/core/utils/patch";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {WebClient} from "@web/webclient/webclient";
import {NavBar} from "@web/webclient/navbar/navbar";
import {
    HOME_MENU_ACTION_TAG,
    ENDERASE_LOGO_URL,
    REGISTRY_CARDS,
    buildRegistrySearchDomain,
    getAppHref,
    getRegistryCard,
    normalizeIconData,
} from "../js/utils";

const HOME_MENU_SYSTRAY_KEYS = ["mail.activity_menu", "mail.messaging_menu", "web.user_menu"];
const APP_OPEN_ANIMATION_MS = 220;

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

export class EnderaseHomeMenu extends Component {
    static template = "enderase_theme.HomeMenu";
    static props = ["*"];

    setup() {
        this.menuService = useService("menu");
        this.router = useService("router");
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            isLeaving: false,
            launchingAppId: null,
            registryScope: REGISTRY_CARDS[0].key,
            searchQuery: "",
            registryCounts: {},
        });

        onMounted(async () => {
            document.body.classList.add("o_enderase_home_menu_open");
            cleanHomeMenuRoute(this.router);
            this.env.bus.trigger("MENUS:APP-CHANGED");
            await this.loadRegistryCounts();
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

    get registryCards() {
        return REGISTRY_CARDS.map((card) => ({
            ...card,
            countLabel: this.formatCountLabel(this.state.registryCounts[card.key]),
        }));
    }

    formatCountLabel(count) {
        return count === undefined || count === null ? "—" : String(count);
    }

    getAppHref(app) {
        return getAppHref(app);
    }

    getAppIcon(app) {
        return normalizeIconData(app);
    }

    getRegistryCardClass(card) {
        return {
            o_enderase_home_menu_registry_card: true,
            [`o_enderase_home_menu_registry_card_${card.key}`]: true,
            o_enderase_home_menu_registry_card_active: this.state.registryScope === card.key,
        };
    }

    async loadRegistryCounts() {
        const counts = {};
        await Promise.all(
            REGISTRY_CARDS.map(async (card) => {
                try {
                    const action = await this.actionService.loadAction(card.action);
                    counts[card.key] = await this.orm.searchCount(
                        "res.partner",
                        action.domain || []
                    );
                } catch {
                    counts[card.key] = 0;
                }
            })
        );
        this.state.registryCounts = counts;
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.openRegistrySearch();
        }
    }

    onScopeChange(ev) {
        this.state.registryScope = ev.target.value;
    }

    async openRegistry(scope = this.state.registryScope) {
        this.state.registryScope = scope;
        const card = getRegistryCard(scope);
        await this._openRegistryAction(card.action, this.state.searchQuery);
    }

    async openRegistrySearch() {
        const card = getRegistryCard(this.state.registryScope);
        await this._openRegistryAction(card.action, this.state.searchQuery);
    }

    async _openRegistryAction(actionXmlId, query) {
        if (this.state.isLeaving) {
            return;
        }
        this.state.isLeaving = true;
        const searchDomain = buildRegistrySearchDomain(query);
        try {
            const action = await this.actionService.loadAction(actionXmlId);
            const baseDomain = action.domain || [];
            action.domain = searchDomain.length
                ? Domain.and([baseDomain, searchDomain]).toList()
                : baseDomain;
            await this.actionService.doAction(action, {clearBreadcrumbs: true});
        } catch {
            this.state.isLeaving = false;
        }
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
