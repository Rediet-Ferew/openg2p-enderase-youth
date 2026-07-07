/** @odoo-module **/

import {Component, onWillStart, useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {ListController} from "@web/views/list/list_controller";

export class EnderaseListKpi extends Component {
    static template = "enderase_theme.ListKpi";
    static props = {
        resModel: {type: String, optional: true},
        total: {type: Number, optional: true},
        pageCount: {type: Number, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.state = useState({active: null, inactive: null});

        onWillStart(async () => {
            const model = this.props.resModel;
            if (!model) {
                return;
            }
            try {
                const fields = await this.orm.call(model, "fields_get", [], {
                    attributes: ["type"],
                });
                if ("active" in fields) {
                    this.state.active = await this.orm.searchCount(model, [["active", "=", true]]);
                    this.state.inactive = await this.orm.searchCount(model, [["active", "=", false]]);
                }
            } catch {
                // Custom models may restrict fields_get — skip optional KPIs
            }
        });
    }

    get cards() {
        const total = this.props.total ?? 0;
        const pageCount = this.props.pageCount ?? 0;
        const cards = [
            {label: "Total", value: total, variant: "gold"},
            {label: "On Page", value: pageCount, variant: "cream"},
        ];
        if (this.state.active !== null) {
            cards.push({label: "Active", value: this.state.active, variant: "cream"});
        }
        if (this.state.inactive !== null) {
            cards.push({label: "Inactive", value: this.state.inactive, variant: "gold"});
        }
        // Storyteller alternation: gold, cream, cream, gold
        const tones = ["gold", "cream", "cream", "gold"];
        return cards.slice(0, 4).map((card, index) => ({
            ...card,
            variant: tones[index] || card.variant,
        }));
    }
}

ListController.components = {
    ...ListController.components,
    EnderaseListKpi,
};
