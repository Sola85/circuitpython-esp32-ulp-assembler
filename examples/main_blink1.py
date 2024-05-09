"""
A example that blinks an LED connected to board.IO13 from the ULP. 

In order to change the pin that does the blinking, one needs to change:
- RTC_IO_TOUCH_PAD13_REG
- RTCIO_GPIO13_CHANNEL

In order to switch to an ESP32 or ESP32S2 on  needs to change:
- DR_REG_RTCIO_BASE
- The compile target in the call to src_to_binary
"""

from esp32_ulp import src_to_binary
import espulp
import memorymap
import board
from time import sleep


source = """
# constants from:
# https://github.com/espressif/esp-idf/blob/v5.0.2/components/soc/esp32s2/include/soc/reg_base.h
#define DR_REG_RTCIO_BASE            0x60008400 #for esp32s3. use 0x3f408400 for esp32s2

# constants from:
# https://github.com/espressif/esp-idf/blob/v5.0.2/components/soc/esp32s2/include/soc/rtc_io_reg.h
#define RTC_IO_TOUCH_PAD13_REG        (DR_REG_RTCIO_BASE + 0xB8)
#define RTC_IO_TOUCH_PAD13_MUX_SEL_M  (BIT(19))
#define RTC_GPIO_OUT_REG             (DR_REG_RTCIO_BASE + 0x0)
#define RTC_GPIO_ENABLE_REG          (DR_REG_RTCIO_BASE + 0xc)
#define RTC_GPIO_ENABLE_S            10
#define RTC_GPIO_OUT_DATA_S          10

# constants from:
# https://github.com/espressif/esp-idf/blob/v5.0.2/components/soc/esp32s2/include/soc/rtc_io_channel.h
#define RTCIO_GPIO13_CHANNEL          13

# When accessed from the RTC module (ULP) GPIOs need to be addressed by their channel number
.set gpio, RTCIO_GPIO13_CHANNEL
.set token, 0xcafe  # magic token

.text
magic: .long 0
state: .long 0

.global entry
entry:
  # load magic flag
  move r0, magic
  ld r1, r0, 0

  # test if we have initialised already
  sub r1, r1, token
  jump after_init, eq  # jump if magic == token (note: "eq" means the last instruction (sub) resulted in 0)

init:
  # connect GPIO to ULP (0: GPIO connected to digital GPIO module, 1: GPIO connected to analog RTC module)
  WRITE_RTC_REG(RTC_IO_TOUCH_PAD13_REG, RTC_IO_TOUCH_PAD13_MUX_SEL_M, 1, 1);

  # GPIO shall be output, not input (this also enables a pull-down by default)
  WRITE_RTC_REG(RTC_GPIO_ENABLE_REG, RTC_GPIO_ENABLE_S + gpio, 1, 1)

  # store that we're done with initialisation
  move r0, magic
  move r1, token
  st r1, r0, 0

after_init:
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
ulp.set_wakeup_period(0, 500000) # wake up every 500 000us = 0.5s
ulp.run(binary, entrypoint=8, pins=[board.IO13]) # entrypoint = 8 because we have 2 variables ('magic' and 'state')
                                                 # before the main entry, each consisting of 4 bytes.

state_variable = memorymap.AddressRange(start=0x50000004, length=4)
while True:
    print(int.from_bytes(state_variable[:], "little"))
    sleep(0.5)