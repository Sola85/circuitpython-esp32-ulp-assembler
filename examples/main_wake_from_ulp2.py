"""
An example demonstrating the capability of the ULP to wake the main chip.

Here we use the ULP to emulate a gpio interrupt. We blink an LED 3 times on the main cpu 
and then go to sleep. 
The ULP reads IO0 10 times per second and if the pin goes low, it wakes up the main cpu.
"""

import board
from esp32_ulp import src_to_binary, Register
from esp32_ulp import soc_s3 as soc
import time
import espulp
from digitalio import DigitalInOut
from alarm import exit_and_deep_sleep_until_alarms, wake_alarm

source = """\

#define DR_REG_RTCIO_BASE            0x60008400                 #for esp32s3. use 0x3f408400 for esp32s2
#define RTC_GPIO_OUT_REG             (DR_REG_RTCIO_BASE + 0x0)
#define RTC_GPIO_OUT_DATA_S          10
#define RTC_GPIO_IN_REG              (DR_REG_RTCIO_BASE + 0x24)

#define DR_REG_RTCCNTL_BASE                     0x60008000
#define RTC_CNTL_LOW_POWER_ST_REG          (DR_REG_RTCCNTL_BASE + 0xD0)
#define RTC_CNTL_RDY_FOR_WAKEUP    (BIT(19))
#define button 0

entry:
            READ_RTC_REG(RTC_GPIO_IN_REG, 10 + button, 1)
            and r0, r0, 1
            jump check_wakeup, eq   # wake main cpu if r0 == 0

            # halt ULP co-processor (until it gets woken up again)
            halt

check_wakeup:                           // Read RTC_CNTL_RDY_FOR_WAKEUP and RTC_CNTL_MAIN_STATE_IN_IDLE bit
          READ_RTC_REG(RTC_CNTL_LOW_POWER_ST_REG, 27, 1)
          MOVE r1, r0                   // Copy result in to r1
          READ_RTC_FIELD(RTC_CNTL_LOW_POWER_ST_REG, RTC_CNTL_RDY_FOR_WAKEUP)
          OR r0, r0, r1
          JUMP check_wakeup, eq         // Retry until either of the bit are set
          WAKE                          // Trigger wake up
          jump trap

trap:
    nop
    jump trap

"""
print("\n", wake_alarm)


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

ulp.set_wakeup_period(0, 100000)
ulp.run(binary, entrypoint=0, pins=[board.IO0])

led = DigitalInOut(board.IO13) # Led to indicate when main cpu is running and when it is sleeping
led.switch_to_output()

# Blink so we see the main cpu in awake
for _ in range(3):
    led.value = not led.value
    time.sleep(1)

# sleep until ulp wakes us up
led.value = 0
exit_and_deep_sleep_until_alarms(espulp.ULPAlarm(ulp))



