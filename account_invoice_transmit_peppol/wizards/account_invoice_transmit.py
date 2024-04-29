# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountInvoiceSent(models.TransientModel):
    _inherit = "account.invoice.transmit"

    transmit_peppol_invoice_ids = fields.Many2many(
        "account.move",
        compute="_compute_transmit_peppol_invoice_ids",
    )
    count_transmit_peppol = fields.Integer(
        "Total by peppol",
        compute="_compute_count_transmit_peppol",
    )

    @api.depends("transmit_invoice_ids")
    def _compute_transmit_peppol_invoice_ids(self):
        self.transmit_peppol_invoice_ids = self.transmit_invoice_ids.filtered(
            lambda r: r.transmit_method_code == "peppol"
        )

    @api.depends("transmit_peppol_invoice_ids")
    def _compute_count_transmit_peppol(self):
        self.count_transmit_peppol = len(self.transmit_peppol_invoice_ids)

    def button_peppol(self):
        invoices = self.transmit_peppol_invoice_ids
        description = _("Mass generating invoice for peppol sending")
        invoices.with_delay(
            description=description,
            priority=40,
            channel="root.invoice_transmit.peppol",
        )._transmit_invoice_by_peppol()
        self.env.user.notify_info(
            _("Invoices will be sent by peppol in the background.")
        )
        return {"type": "ir.actions.act_window_close"}
