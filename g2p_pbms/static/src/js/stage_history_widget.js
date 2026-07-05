/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillUnmount } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { usePopover } from "@web/core/popover/popover_hook";

class StageHistoryPopover extends Component {
    static template = "g2p_pbms.StageHistoryPopover";
    static props = {
        stages: Array,
        onPopoverMouseEnter: { type: Function, optional: true },
        onPopoverMouseLeave: { type: Function, optional: true },
        close: Function,
    };
}

class StageHistoryWidget extends Component {
    static template = "g2p_pbms.StageHistoryWidget";
    static props = { ...standardFieldProps };
    static relatedFields = [
        { name: "stage_number", type: "integer" },
        { name: "stage_name", type: "char" },
        { name: "status", type: "selection", selection: [] },
        { name: "acted_by", type: "many2one", relation: "res.users" },
        { name: "acted_at", type: "datetime" },
        { name: "reason", type: "text" },
    ];

    setup() {
        this._closeTimerId = null;
        this.popover = usePopover(StageHistoryPopover, {
            position: "right-start",
            closeOnClickAway: true,
        });
        onWillUnmount(() => clearTimeout(this._closeTimerId));
    }

    get stages() {
        const list = this.props.record.data[this.props.name];
        if (!list || !list.records) return [];
        return list.records.map((r) => ({
            stage_number: r.data.stage_number || "",
            stage_name: r.data.stage_name || "",
            status: r.data.status || "",
            acted_by: Array.isArray(r.data.acted_by) ? r.data.acted_by[1] : "",
            acted_at: r.data.acted_at
                ? r.data.acted_at.toFormat
                    ? r.data.acted_at.toFormat("dd/MM/yyyy")
                    : String(r.data.acted_at).slice(0, 10)
                : "",
            reason: r.data.reason || "",
        }));
    }

    get label() {
        const n = this.stages.length;
        return n ? `${n} stage${n !== 1 ? "s" : ""}` : "—";
    }

    get badgeClass() {
        const stages = this.stages;
        if (!stages.length) return "badge text-bg-secondary";
        const last = stages[stages.length - 1];
        if (last.status === "APPROVED") return "badge text-bg-success";
        if (last.status === "REJECTED") return "badge text-bg-danger";
        if (last.status === "PENDING") return "badge text-bg-warning";
        return "badge text-bg-secondary";
    }

    onMouseEnter(ev) {
        clearTimeout(this._closeTimerId);
        this._closeTimerId = null;
        const stages = this.stages;
        if (!stages.length) return;
        this.popover.open(ev.currentTarget, {
            stages,
            onPopoverMouseEnter: () => {
                clearTimeout(this._closeTimerId);
                this._closeTimerId = null;
            },
            onPopoverMouseLeave: () => this._scheduleClose(),
        });
    }

    onMouseLeave() {
        this._scheduleClose();
    }

    _scheduleClose() {
        this._closeTimerId = setTimeout(() => {
            this.popover.close();
            this._closeTimerId = null;
        }, 250);
    }
}

registry.category("fields").add("stage_history_widget", {
    component: StageHistoryWidget,
    displayName: "Stage History Widget",
    supportedTypes: ["one2many"],
});
