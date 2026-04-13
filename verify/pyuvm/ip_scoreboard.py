"""SPI scoreboard — compares TX transactions from DUT and reference model."""

from cf_verify.base.scoreboard import scoreboard
from ip_item.spi_item import spi_item


class spi_scoreboard(scoreboard):
    async def _compare_ip(self):
        """Compare TX transactions; RX is verified via register reads in loopback."""
        while True:
            dut_tr = await self.ip_dut_fifo.get()
            if hasattr(dut_tr, "direction") and dut_tr.direction == spi_item.TX:
                ref_tr = await self.ip_ref_fifo.get()
                self._check("IP", dut_tr, ref_tr)
