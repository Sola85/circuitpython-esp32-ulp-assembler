"""
An alternative implementation of the blink example.

Here we initialize the GPIO from within circuitpython, so the assembly looks a bit simpler.
"""

from esp32_ulp import src_to_binary, Register
import esp32_ulp.soc_s3 as soc
import espulp
import memorymap
import board
from time import sleep


source = """
#define DR_REG_RTCIO_BASE            0x60008400                 #for esp32s3. use 0x3f408400 for esp32s2
#define RTC_GPIO_OUT_REG             (DR_REG_RTCIO_BASE + 0x0)
#define RTC_GPIO_OUT_DATA_S          10

.set gpio, 13

.text
state: .long 0

.global entry
entry:
  move r1, state
  ld r0, r1, 0

  move r2, 1
  sub r0, r2, r0  # toggle state
  st r0, r1, 0  # store updated state

  jumpr on, 0, gt  # if r0 (state) > 0, jump to 'on'
  jump off  # else jump to 'off'

on:
  # turn on led (set GPIO)
  WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + gpio, 1, 1)
  jump exit

off:
  # turn off led (clear GPIO)
  WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + gpio, 1, 0)
  jump exit

exit:
  halt  # go back to sleep until next wakeup period
"""


binary = src_to_binary(source, cpu="esp32s2")  # cpu is esp32 or esp32s2


ulp = espulp.ULP()
ulp.halt()

pin_number = 13
RTC_IO_TOUCH_PAD13_REG = Register(soc.DR_REG_RTCIO_BASE + 0xB8)
RTC_IO_TOUCH_PAD13_REG.set_bit(19) # connect GPIO to ULP (bit cleared: GPIO connected to digital GPIO module, bit set: GPIO connected to analog RTC module) (19 = RTC_IO_TOUCH_PAD13_MUX_SEL_M)
RTC_GPIO_ENABLE_REG = Register(soc.DR_REG_RTCIO_BASE + 0x0C)
RTC_GPIO_ENABLE_REG.set_bit(10 + pin_number) # GPIO shall be output, not input (this also enables a pull-down by default)

ulp.set_wakeup_period(0, 500000)
ulp.run(binary, entrypoint=4, pins=[board.IO13])

state_variable = memorymap.AddressRange(start=0x50000000, length=4)
while True:
    print(int.from_bytes(state_variable[:], "little"))
    sleep(0.5)