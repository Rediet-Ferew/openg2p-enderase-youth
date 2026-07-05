/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { View } from "@web/views/view";

class ApprovalsAction extends Component {
    static template = "g2p_pbms.ApprovalsAction";
    static components = { View };
    static props = ["*"];

    setup() {
        this.rpc = useService("rpc");
        this.user = useService("user");
        const defaultTab = (this.props.action && this.props.action.params && this.props.action.params.default_tab) || "queue";
        this.state = useState({ activeTab: defaultTab });
        this.queueDomain = [];

        onWillStart(async () => {
            this.queueDomain = await this.rpc(
                "/web/dataset/call_kw/g2p.workflow.pending.stage/get_approval_queue_domain",
                {
                    model: "g2p.workflow.pending.stage",
                    method: "get_approval_queue_domain",
                    args: [],
                    kwargs: {},
                }
            );
            // Resolve the tree view ID so the View component uses our custom tree
            const result = await this.rpc("/web/dataset/call_kw/ir.model.data/check_object_reference", {
                model: "ir.model.data",
                method: "check_object_reference",
                args: ["g2p_pbms", "view_g2p_approval_queue_tree"],
                kwargs: {},
            });
            this.queueTreeViewId = result ? result[1] : false;
            const histResult = await this.rpc("/web/dataset/call_kw/ir.model.data/check_object_reference", {
                model: "ir.model.data",
                method: "check_object_reference",
                args: ["g2p_pbms", "view_g2p_approval_history_tree"],
                kwargs: {},
            });
            this.historyTreeViewId = histResult ? histResult[1] : false;
        });
    }

    onTabClick(tab) {
        this.state.activeTab = tab;
    }

    get queueViewProps() {
        return {
            type: "list",
            resModel: "g2p.workflow.pending.stage",
            domain: this.queueDomain,
            context: { approval_queue: true },
            viewId: this.queueTreeViewId || false,
            noContentHelp: "No pending approvals.",
            allowSelectors: false,
            selectRecord: () => {},
        };
    }

    get historyViewProps() {
        return {
            type: "list",
            resModel: "g2p.workflow.stage.history",
            domain: [
                ["acted_by", "=", this.user.userId],
                ["status", "in", ["APPROVED", "REJECTED"]],
            ],
            viewId: this.historyTreeViewId || false,
            context: {},
            noContentHelp: "No approval history.",
            allowSelectors: false,
            selectRecord: () => {},
        };
    }
}

registry.category("actions").add("g2p_approvals_tabbed", ApprovalsAction);
