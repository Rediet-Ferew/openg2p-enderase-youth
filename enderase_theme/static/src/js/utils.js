/** @odoo-module **/

export const HOME_MENU_ACTION_TAG = "enderase_theme.home_menu";
export const ENDERASE_LOGO_URL = "/enderase_theme/static/src/img/enderase-icon.png";
export const HOME_MENU_PAGE_BACKGROUND = "#f2f1ec";

export const REGISTRY_CARDS = [
    {
        key: "members",
        label: "Members",
        action: "g2p_enderase_youth_registry.action_enderase_members",
    },
    {
        key: "beneficiaries",
        label: "Beneficiaries",
        action: "g2p_enderase_youth_registry.action_enderase_beneficiaries",
    },
    {
        key: "startups",
        label: "Startups",
        action: "g2p_enderase_youth_registry.action_enderase_startups",
    },
    {
        key: "associations",
        label: "Associations",
        action: "g2p_enderase_youth_registry.action_enderase_associations",
    },
    {
        key: "communities",
        label: "Communities",
        action: "g2p_enderase_youth_registry.action_enderase_communities",
    },
    {
        key: "organizations",
        label: "Organizations",
        action: "g2p_enderase_youth_registry.action_enderase_organizations",
    },
];

export function getRegistryCard(key) {
    return REGISTRY_CARDS.find((card) => card.key === key) || REGISTRY_CARDS[0];
}

export function buildRegistrySearchDomain(query) {
    const term = query.trim();
    if (!term) {
        return [];
    }
    return [
        "|",
        "|",
        "|",
        ["name", "ilike", term],
        ["enderase_registry_id", "ilike", term],
        ["phone", "ilike", term],
        ["email", "ilike", term],
    ];
}
const NAV_GROUP_RULES = [
    {label: "Registry", match: /registry|beneficiar|member|organization|g2p|social|registrant/i},
    {label: "Programs", match: /skill|startup|program|disburs/i},
    {label: "Insights", match: /dashboard|report|embed|ati|insight|analytic/i},
];

export function normalizeIconData(app) {
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

export function groupApps(apps) {
    const buckets = new Map();
    const ensure = (label) => {
        if (!buckets.has(label)) {
            buckets.set(label, []);
        }
        return buckets.get(label);
    };

    for (const app of apps) {
        const haystack = `${app.name || ""} ${app.xmlid || ""}`;
        const rule = NAV_GROUP_RULES.find((entry) => entry.match.test(haystack));
        ensure(rule ? rule.label : "Applications").push(app);
    }

    const order = ["Registry", "Programs", "Insights", "Applications"];
    return order
        .filter((label) => buckets.has(label))
        .map((label) => ({label, apps: buckets.get(label)}));
}

export function getAppHref(app) {
    const hrefParts = [`menu_id=${app.id}`];
    if (app.actionID) {
        hrefParts.push(`action=${app.actionID}`);
    }
    return `#${hrefParts.join("&")}`;
}
