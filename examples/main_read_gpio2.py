"""
Same as the previous example, but we initialize the GPIO from circuitpython, 
hence the assembly is a bit simpler.

This example is for the esp32s3. Change the following addresses for other targets:
- DR_REG_RTCIO_BASE
- DR_REG_SENS_BASE
"""

import board
from esp32_ulp import src_to_binary, Register
import esp32_ulp.soc_s3 as soc
import memorymap
import time
import espulp

source = """\
#define DR_REG_RTCIO_BASE            0x60008400
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)

.set channel, 0

state:      .long 0

entry:
            # read the GPIO's current state into r0
            READ_RTC_REG(RTC_GPIO_IN_REG, 10 + channel, 1)

            # set r3 to the memory address of "state"
            move r3, state

            # store what was read into r0 into the "state" variable
            st r0, r3, 0

            # halt ULP co-processor (until it gets woken up again)
            halt
"""

binary = src_to_binary(source, cpu="esp32s2")  # cpu is esp32 or esp32s2


ulp = espulp.ULP()
ulp.halt()


SENS_SAR_PERI_CLK_GATE_CONF_REG = Register(soc.DR_REG_SENS_BASE+0x104)
RTC_IO_TOUCH_PAD0_REG = Register(soc.DR_REG_RTCIO_BASE + 0x84)
RTC_IN_REG = Register(soc.DR_REG_RTCIO_BASE + 0x24)

SENS_SAR_PERI_CLK_GATE_CONF_REG.set_bit(31) # enable IOMUX clock
RTC_IO_TOUCH_PAD0_REG.clear_bit(28)         # Disable pull-down
RTC_IO_TOUCH_PAD0_REG.set_bit(27)           # Enable pull-up
RTC_IO_TOUCH_PAD0_REG.set_bit(19)           # Connect GPIO to rtc subsystem
RTC_IO_TOUCH_PAD0_REG.set_bit(13)           # Set GPIO to Input

ulp.set_wakeup_period(0, 50000)
ulp.run(binary, entrypoint=4, pins=[board.IO0])

state_variable = memorymap.AddressRange(start=0x50000000, length=4)

while True:
    print(int.from_bytes(state_variable[:], "little"))
    time.sleep(1)