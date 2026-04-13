"""SPI loopback sequence — sends via TX, reads back from RXDATA via loopback."""

import random

from pyuvm import uvm_sequence, ConfigDB
from cocotb.triggers import ClockCycles

from cf_verify.bus_env.bus_seq_lib import write_reg_seq, read_reg_seq
from seq_lib.spi_config_seq import spi_config_seq


class spi_loopback_seq(uvm_sequence):
    def __init__(self, name="spi_loopback_seq"):
        super().__init__(name)

    async def body(self):
        regs = ConfigDB().get(None, "", "bus_regs")
        addr = regs.reg_name_to_address
        dut = ConfigDB().get(None, "", "DUT")

        config = spi_config_seq("config", rx_en=1)
        await config.start(self.sequencer)

        pr = regs.read_reg_value("PR")
        bit_cyc = (pr + 1) * 16

        sent_data = []
        for _ in range(4):
            data = random.randint(0, 0xFF)
            sent_data.append(data)
            await write_reg_seq("tx_wr", addr["TXDATA"], data).start(self.sequencer)
            await ClockCycles(dut.CLK, bit_cyc * 12)

        # Read back from RXDATA (loopback: MISO = MOSI)
        for expected in sent_data:
            rx = await read_reg_seq("rx_rd", addr["RXDATA"]).start(self.sequencer)
