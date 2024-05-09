"""
This is a combination of the read_gpio and the blink example.

The ULP blinks the LED on IO13 until IO0 goes low.

To demonstrate the capability of the ULP to run while the main cpu is sleeping,
we directly go to sleep mode after everything is set up.
"""

import board
from esp32_ulp import src_to_binary, Register
import esp32_ulp.soc_s3 as soc
import espulp
import alarm

source = """\
#define DR_REG_RTCIO_BASE            0x60008400                 #for esp32s3. use 0x3f408400 for esp32s2
#define RTC_GPIO_OUT_REG             (DR_REG_RTCIO_BASE + 0x0)
#define RTC_GPIO_OUT_DATA_S          10

#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)

.set channel, 0

.set led, 13

state:      .long 0

entry:
    move r1, state
    ld r0, r1, 0

    move r2, 1
    sub r0, r2, r0  # toggle state
    st r0, r1, 0  # store updated state

    move r2, r0
    

    # read the GPIO's current state into r0
    READ_RTC_REG(RTC_GPIO_IN_REG, 10 + channel, 1)
    and r0, r2, r0

    jumpr on, 0, gt  # if r0 (state) > 0, jump to 'on'
    jump off  # else jump to 'off'

off:
    # turn off led (clear GPIO)
    WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + led, 1, 0)
    halt

on:
    # turn on led (set GPIO)
    WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + led, 1, 1)
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

pin_number = 13
RTC_IO_TOUCH_PAD13_REG = Register(soc.DR_REG_RTCIO_BASE + 0xB8)
RTC_IO_TOUCH_PAD13_REG.set_bit(19) # connect GPIO to ULP (bit cleared: GPIO connected to digital GPIO module, bit set: GPIO connected to analog RTC module) (19 = RTC_IO_TOUCH_PAD13_MUX_SEL_M)
RTC_GPIO_ENABLE_REG = Register(soc.DR_REG_RTCIO_BASE + 0x0C)
RTC_GPIO_ENABLE_REG.set_bit(10 + pin_number) # GPIO shall be output, not input (this also enables a pull-down by default)

ulp.set_wakeup_period(0, 500000)
ulp.run(binary, entrypoint=4, pins=[board.IO0, board.IO13])


alarm.exit_and_deep_sleep_until_alarms()
