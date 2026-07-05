/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { DomainSelector } from "@web/core/domain_selector/domain_selector";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class G2PBeneficiariesComponent extends Component {
    static template = "g2p_beneficiaries_info_tpl";
    static components = { DomainSelector };
    static props = {
        context: { type: Object, optional: true },
        resModel: { type: String, optional: true },
        record: { type: Object, optional: true },
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({
            title: _t("Beneficiaries"),
            records: [],
            page: 1,
            pageSize: 20,
            totalCount: 0,
            totalPages: 1,
            target_registry: this.props.record?.data?.target_registry,
            searched: false,
            domain: "[]",
        });
        this.orm = useService("orm");
    }

    onDomainChange(newDomain) {
        this.state.domain = newDomain;
        this.render();
    }

    searchRegistrants() {
        this.state.searched = true;
        this.state.page = 1;
        this._fetchRecords();
    }

    async _fetchRecords() {
        const wizardId = this.props.record?.resId;
        if (!wizardId) {
            this.state.records = [];
            this.state.totalCount = 0;
            this.state.totalPages = 1;
            return;
        }

        const result = await this.orm.call(
            "g2p.bgtask.summary.wizard",
            "get_beneficiaries",
            [wizardId, this.state.page, this.state.pageSize, this.state.domain],
            {},
        );
        const responsePayload = result?.response_body?.response_payload || result?.message || result || {};

        this.state.records = responsePayload.beneficiaries || responsePayload.records || [];
        this.state.totalCount =
            responsePayload.total_beneficiary_count ||
            responsePayload.beneficiary_count ||
            responsePayload.total_count ||
            0;
        this.state.totalPages = Math.ceil(this.state.totalCount / this.state.pageSize) || 1;
    }

    async nextPage() {
        if (this.state.page < this.state.totalPages) {
            this.state.page++;
            await this._fetchRecords();
        }
    }

    async prevPage() {
        if (this.state.page > 1) {
            this.state.page--;
            await this._fetchRecords();
        }
    }
}

export const g2pBeneficiariesWidget = {
    component: G2PBeneficiariesComponent,
    extractProps({ attrs }, dynamicInfo) {
        return {
            resModel: attrs.model,
            context: dynamicInfo.context,
        };
    },
};

registry.category("view_widgets").add("g2p_beneficiaries_widget", g2pBeneficiariesWidget);
