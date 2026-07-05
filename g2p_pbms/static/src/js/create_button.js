/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart } from "@odoo/owl";

const NO_OPEN_MODELS = ["g2p.enrollment.cycle", "g2p.disbursement.cycle"];

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService("orm");
        this.user = useService("user");

        this.permissions = useState({
            canCreateAgency: false,
            canCreateWarehouse: false,
            canCreateSponsorBank: false,
            canCreateBenefitCode: false,
            canCreateProgram: false,
            canCreateGeography: false,
        });

        this.programConfigViewId = null;

        // Load groups before rendering
        onWillStart(async () => {
            this.permissions.canCreateAgency = await this.user.hasGroup("g2p_pbms.group_agency_editor");
            this.permissions.canCreateWarehouse = await this.user.hasGroup("g2p_pbms.group_warehouse_editor");
            this.permissions.canCreateSponsorBank = await this.user.hasGroup("g2p_pbms.group_warehouse_editor");
            this.permissions.canCreateBenefitCode = await this.user.hasGroup("g2p_pbms.group_benefit_code_editor");
            this.permissions.canCreateGeography = await this.user.hasGroup("g2p_pbms.group_geography_editor");

            this.permissions.canCreateProgram = await this.user.hasGroup("g2p_pbms.group_program_super_administration");

            const configViews = await this.orm.searchRead(
                "ir.ui.view",
                [["name", "=", "g2p.programs.config.form"]],
                ["id"],
                { limit: 1 }
            );
            if (configViews.length) {
                this.programConfigViewId = configViews[0].id;
            }
        });
    },

    load_agency_wizard() {
        this.action.doAction({
            name: "Agency",
            type: "ir.actions.act_window",
            res_model: "g2p.agency",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: { create: false, agency_form_edit: true },
        });
    },

    async load_warehouse_wizard() {
        const action = await this.orm.call("g2p.warehouse", "action_open_create_warehouse", [[]]);
        this.action.doAction(action);
    },

    async load_sponsor_bank_wizard() {
        const action = await this.orm.call("g2p.warehouse", "action_open_create_sponsor_bank", [[]]);
        this.action.doAction(action);
    },

    load_benefit_code_wizard() {
        this.action.doAction({
            name: "Benefit Codes",
            type: "ir.actions.act_window",
            res_model: "g2p.benefit.codes",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: { create: false, benefit_code_form_edit: true },
        });
    },

    load_program_wizard() {
        this.action.doAction({
            name: "Program",
            type: "ir.actions.act_window",
            res_model: "g2p.program.definition",
            view_mode: "form",
            views: [[this.programConfigViewId || false, "form"]],
            target: "current",
            context: {
                create: false,
                program_form_edit: true,
                program_form_create: true,
                program_view_mode: "config",
            },
        });
    },

    load_administrative_area_large_wizard() {
        this.action.doAction({
            name: "Administrative Area (Large)",
            type: "ir.actions.act_window",
            res_model: "g2p.administrative.area.large",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: { create: false, area_form_edit: true },
        });
    },

    openRecord(record) {
        if (NO_OPEN_MODELS.includes(this.props.resModel)) {
            return;
        }
        return super.openRecord(record);
    },

    load_administrative_area_small_wizard() {
        this.action.doAction({
            name: "Administrative Area (Small)",
            type: "ir.actions.act_window",
            res_model: "g2p.administrative.area.small",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: { create: false, area_form_edit: true },
        });
    },

    async load_enrollment_cycle_wizard() {
        const searchContext = this.env.searchModel && this.env.searchModel.context || {};
        const additionalContext = {};
        if (searchContext.default_program_id) {
            additionalContext.default_program_id = searchContext.default_program_id;
        }
        const action = await this.orm.call(
            "g2p.enrollment.cycle",
            "action_open_create_wizard",
            [[]],
            { context: additionalContext }
        );
        this.action.doAction(action);
    },

    async load_disbursement_cycle_wizard() {
        const searchContext = this.env.searchModel && this.env.searchModel.context || {};
        const additionalContext = {};
        if (searchContext.default_program_id) {
            additionalContext.default_program_id = searchContext.default_program_id;
        }
        const action = await this.orm.call(
            "g2p.disbursement.cycle",
            "action_open_create_wizard",
            [[]],
            { context: additionalContext }
        );
        this.action.doAction(action);
    },
});
