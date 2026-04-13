"""SPI FIFO sequence — tests FIFO full, empty, threshold, and flush."""

import random

from pyuvm import uvm_sequence, ConfigDB
from cocotb.triggers import ClockCycles

from cf_verify.bus_env.bus_seq_lib import write_reg_seq, read_reg_seq
from seq_lib.spi_config_seq import spi_config_seq


class spi_fifo_seq(uvm_sequence):
    async def body(self):
        regs = ConfigDB().get(None, "", "bus_regs")
        addr = regs.reg_name_to_address
        dut = ConfigDB().get(None, "", "DUT")

        config = spi_config_seq("config", im=0x3F, rx_en=1)
        await config.start(self.sequencer)

        pr = regs.read_reg_value("PR")
        bit_cyc = (pr + 1) * 16

        # Set TX FIFO threshold to 4
        if "TX_FIFO_THRESHOLD" in addr:
            await write_reg_seq("tx_thr", addr["TX_FIFO_THRESHOLD"], 4).start(self.sequencer)

        # Set RX FIFO threshold to 4
        if "RX_FIFO_THRESHOLD" in addr:
            await write_reg_seq("rx_thr", addr["RX_FIFO_THRESHOLD"], 4).start(self.sequencer)

        # Fill TX FIFO to capacity (16 entries) and check level
        for i in range(16):
            await write_reg_seq("tx", addr["TXDATA"], i & 0xFF).start(self.sequencer)

        # Check TX FIFO level
        if "TX_FIFO_LEVEL" in addr:
            await read_reg_seq("tx_lvl", addr["TX_FIFO_LEVEL"]).start(self.sequencer)

        # Overfill TX FIFO
        for i in range(4):
            await write_reg_seq("tx_overflow", addr["TXDATA"], 0xAA).start(self.sequencer)

        # Read RIS for FIFO flags
        await read_reg_seq("ris", addr["RIS"]).start(self.sequencer)

        # Read STATUS for FIFO status bits
        await read_reg_seq("status", addr["STATUS"]).start(self.sequencer)

        # Flush TX FIFO
        if "TX_FIFO_FLUSH" in addr:
            await write_reg_seq("flush_tx", addr["TX_FIFO_FLUSH"], 1).start(self.sequencer)

        # Flush RX FIFO
        if "RX_FIFO_FLUSH" in addr:
            await write_reg_seq("flush_rx", addr["RX_FIFO_FLUSH"], 1).start(self.sequencer)

        # Verify FIFOs are empty
        if "TX_FIFO_LEVEL" in addr:
            await read_reg_seq("tx_lvl_0", addr["TX_FIFO_LEVEL"]).start(self.sequencer)
        if "RX_FIFO_LEVEL" in addr:
            await read_reg_seq("rx_lvl_0", addr["RX_FIFO_LEVEL"]).start(self.sequencer)

        # Verify STATUS shows empty after flush
        await read_reg_seq("status_post", addr["STATUS"]).start(self.sequencer)
