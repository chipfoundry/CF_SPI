"""SPI interrupt sequence — exercises all interrupt sources and verifies IM/IC."""

import random

from pyuvm import uvm_sequence, ConfigDB
from cocotb.triggers import ClockCycles

from cf_verify.bus_env.bus_seq_lib import write_reg_seq, read_reg_seq
from seq_lib.spi_config_seq import spi_config_seq


class spi_interrupt_seq(uvm_sequence):
    async def body(self):
        regs = ConfigDB().get(None, "", "bus_regs")
        addr = regs.reg_name_to_address
        dut = ConfigDB().get(None, "", "DUT")

        # Configure SPI with all interrupts enabled (6 flags: TXE,TXF,RXE,RXF,TXB,RXA)
        config = spi_config_seq("config", im=0x3F)
        await config.start(self.sequencer)

        pr = regs.read_reg_value("PR")
        bit_cyc = (pr + 1) * 16

        # TX full: fill the TX FIFO to capacity (16 entries for FAW=4)
        for i in range(17):
            await write_reg_seq("tx_fill", addr["TXDATA"], i & 0xFF).start(self.sequencer)

        # Read RIS to check TX full flag
        await read_reg_seq("ris_rd", addr["RIS"]).start(self.sequencer)
        # Read MIS to check masked status
        await read_reg_seq("mis_rd", addr["MIS"]).start(self.sequencer)

        # Clear all interrupts
        await write_reg_seq("ic_clear", addr["IC"], 0x3F).start(self.sequencer)
        # Verify cleared
        await read_reg_seq("ris_check", addr["RIS"]).start(self.sequencer)

        # Test individual interrupt mask bits
        for bit in range(6):
            await write_reg_seq("im_set", addr["IM"], 1 << bit).start(self.sequencer)
            await read_reg_seq("im_rd", addr["IM"]).start(self.sequencer)

        # Restore all interrupts
        await write_reg_seq("im_all", addr["IM"], 0x3F).start(self.sequencer)

        # Wait for existing TX data to drain, then check TX empty interrupt
        await ClockCycles(dut.CLK, bit_cyc * 12 * 17)
        await read_reg_seq("ris_txe", addr["RIS"]).start(self.sequencer)
