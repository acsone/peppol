# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.addons.queue_job.job import identity_exact


class AccountMove(models.Model):
    _inherit = "account.move"

    def _is_transmissible_by_peppol(self):
        """Check if the invoice can be sent by peppol"""
        self.ensure_one()
        return (
            not self.is_move_sent
            and not self.invoice_exported
            and self.transmit_method_code == "peppol"
        )

    def _batch_transmit_invoice_by_peppol(self, commit_interval=10):
        """Mass sending by peppol

        Since sending by Peppol can be time consuming due to the
        communication with external services, we create a separate
        job for each invoice.

        """
        result = []
        cpt = 0
        for invoice in self:
            cpt += 1
            if not invoice._is_transmissible_by_peppol():
                description = _(
                    "Invoice already sent to peppol: %(name)s",
                    name=invoice.name,
                )
            else:
                description = _(
                    "Generating invoice for peppol sending: %(name)s",
                    name=invoice.name,
                )
                invoice.with_delay(
                    description=description,
                    identity_key=identity_exact,
                    priority=40,
                    channel="root.invoice_transmit.peppol",
                )._transmit_invoice_by_peppol()
            if cpt % commit_interval == 0:
                self.env.cr.commit()
            result.append(description)

        return "\n".join(result)

    def _transmit_invoice_by_peppol(self):
        """Sending by peppol"""
        invoices = self.filtered(self._is_transmissible_by_peppol)
        invoices = self._transmit_invoice("peppol")
        return invoices.peppol_export_invoice()
