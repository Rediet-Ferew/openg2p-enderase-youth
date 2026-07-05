/** @odoo-module **/

import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useState, useEffect } from "@odoo/owl";

export class MultiplierFieldWidget extends CharField {
    static template = "g2p_pbms.MultiplierFieldWidget";

    setup() {
        super.setup();
        
        this.state = useState({
            options: []
        });
        
        // Watch for changes in allowed_multipliers
        useEffect(
            () => {
                this.updateOptions();
            },
            () => [this.props.record.data.allowed_multipliers]
        );
        
        // Initial load
        this.updateOptions();
    }
    
    updateOptions() {
        let parsedOptions = [];
        try {
            parsedOptions = JSON.parse(this.props.record.data.allowed_multipliers || "[]");
        } catch (e) {
            console.warn("Invalid allowed_multipliers JSON", e);
        }
        
        this.state.options = parsedOptions.map(([value, label]) => ({ value, label }));
    }
}

registry.category("fields").add("g2p_pbms.multiplier_widget", {
    component: MultiplierFieldWidget,
});
