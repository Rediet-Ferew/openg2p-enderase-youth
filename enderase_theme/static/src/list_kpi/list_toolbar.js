/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import {ListController} from "@web/views/list/list_controller";
import {useEffect} from "@odoo/owl";

function getListChrome(rootEl) {
    if (!rootEl) {
        return {};
    }
    const actionEl = rootEl.closest(".o_action");
    return {
        actionEl,
        controlPanel: actionEl?.querySelector(".o_control_panel .o_control_panel_main"),
        toolbar: rootEl.querySelector(".o_enderase_list_toolbar"),
    };
}

function syncListToolbar(rootEl) {
    const {controlPanel, toolbar} = getListChrome(rootEl);
    if (!controlPanel || !toolbar) {
        return;
    }

    const actions = controlPanel.querySelector(".o_control_panel_actions");
    const navigation = controlPanel.querySelector(".o_control_panel_navigation");
    const hasSearch = actions?.querySelector(".o_cp_searchview");

    if (hasSearch && actions && actions.parentElement === controlPanel) {
        toolbar.appendChild(actions);
    }
    if (navigation && navigation.parentElement === controlPanel) {
        toolbar.appendChild(navigation);
    }

    toolbar.classList.toggle("o_enderase_list_toolbar_ready", toolbar.childElementCount > 0);
}

function restoreListToolbar(rootEl) {
    const {controlPanel, toolbar} = getListChrome(rootEl);
    if (!controlPanel || !toolbar) {
        return;
    }

    for (const child of [...toolbar.children]) {
        if (child.classList.contains("o_control_panel_actions")) {
            controlPanel.appendChild(child);
        } else if (child.classList.contains("o_control_panel_navigation")) {
            controlPanel.appendChild(child);
        }
    }
    toolbar.classList.remove("o_enderase_list_toolbar_ready");
}

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);

        useEffect(
            () => {
                const rootEl = this.rootRef.el;
                if (!rootEl) {
                    return;
                }

                const runSync = () => syncListToolbar(rootEl);
                runSync();

                const {controlPanel} = getListChrome(rootEl);
                let observer;
                if (controlPanel) {
                    observer = new MutationObserver(runSync);
                    observer.observe(controlPanel, {childList: true, subtree: true});
                }

                return () => {
                    observer?.disconnect();
                    restoreListToolbar(rootEl);
                };
            },
            () => [this.rootRef.el]
        );
    },
});
