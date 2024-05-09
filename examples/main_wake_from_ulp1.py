"""
An example demonstrating the capability of the ULP to wake the main chip.

Here we use the ULP to emulate a timer interrupt. The main cpu blinks an LED 3 times,
the goes to sleep. The ULP counts down from 10 and then wakes up the main cpu again.
"""

import board
from esp32_ulp import src_to_binary
import memorymap
import time
import espulp
from digitalio import DigitalInOut
from alarm import exit_and_deep_sleep_until_alarms, wake_alarm

source = """\

#define DR_REG_RTCCNTL_BASE        0x60008000 # for esp32s3, modify for esp32s2
#define RTC_CNTL_LOW_POWER_ST_REG  (DR_REG_RTCCNTL_BASE + 0xD0)
#define RTC_CNTL_RDY_FOR_WAKEUP    (BIT(19))

state:      .long 10

entry:
            # set r3 to the memory address of "state"
            move r3, state

            ld r0, r3, 0            # load data contents ([r3+0]) into r0
            sub r0, r0, 1           # decrement r0
            jump check_wakeup, eq   # wake main cpu if state == 0

            # store contents of r0 into the "state" variable
            st r0, r3, 0

            # halt ULP co-processor (until it gets woken up again)
            halt

check_wakeup:                           // Read RTC_CNTL_RDY_FOR_WAKEUP and RTC_CNTL_MAIN_STATE_IN_IDLE bit
          READ_RTC_REG(RTC_CNTL_LOW_POWER_ST_REG, 27, 1)
          MOVE r1, r0                   // Copy result in to r1
          READ_RTC_FIELD(RTC_CNTL_LOW_POWER_ST_REG, RTC_CNTL_RDY_FOR_WAKEUP)
          OR r0, r0, r1
          JUMP check_wakeup, eq         // Retry until either of the bit are set
          WAKE                          // Trigger wake up
          add r0, r0, 10                // increment state variable, so we dont immediately wake up again.
          st r0, r3, 0
          HALT                          // Stop the ULP program

"""
print("\n", wake_alarm)

binary = src_to_binary(source, cpu="esp32s2")  # cpu is esp32 or esp32s2

ulp = espulp.ULP()
ulp.halt()
ulp.set_wakeup_period(0, 1000000)
ulp.run(binary, entrypoint=4, pins=[])

led = DigitalInOut(board.IO13) # Led to indicate when main cpu is running and when it is sleeping
led.switch_to_output()

state_variable = memorymap.AddressRange(start=0x50000000, length=4)

#Watch state variable decrease and blink led for 3 seconds
for _ in range(3):
    print(int.from_bytes(state_variable[:], "little"))
    led.value = not led.value
    time.sleep(1)

# sleep. now ulp keeps decrementing its state variable and when it hits 0, we will wake up again.
led.value = 0
exit_and_deep_sleep_until_alarms(espulp.ULPAlarm(ulp))



