"""
A third version of the blink example. 

Here we dont rely on the wakeup period to act as a delay. 
Instead we implement the delay on the ULP itself.

Note that this version is less desirable, since the ULP is running continuously 
and hence consumes much more power.
"""


from esp32_ulp import src_to_binary, Register
import esp32_ulp.soc_s3 as soc
import espulp
import board


source = """
#define DR_REG_RTCIO_BASE            0x60008400                 #for esp32s3. use 0x3f408400 for esp32s2
#define RTC_GPIO_OUT_REG             (DR_REG_RTCIO_BASE + 0x0)
#define RTC_GPIO_OUT_DATA_S          10

.set gpio, 13

.text

.global entry
entry:
  # turn on led (set GPIO)
  WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + gpio, 1, 1)
  move r1, 100    # 100 ms delay
  move r2, off
  jump delay

off:
  # turn off led (clear GPIO)
  WRITE_RTC_REG(RTC_GPIO_OUT_REG, RTC_GPIO_OUT_DATA_S + gpio, 1, 0)
  move r1, 1000   # 1000 ms delay
  move r2, entry
  jump delay

delay:
  wait 8000       # 8000 cycles at 8 MHz -> 1 ms 
  sub r1, r1, 1
  jump r2, eq     # if ms count is zero, then return to caller
  jump delay
"""


binary = src_to_binary(source, cpu="esp32s2")  # cpu is esp32 or esp32s2


ulp = espulp.ULP()
ulp.halt()

pin_number = 13
RTC_IO_TOUCH_PAD13_REG = Register(soc.DR_REG_RTCIO_BASE + 0xB8)
RTC_IO_TOUCH_PAD13_REG.set_bit(19) # connect GPIO to ULP (bit cleared: GPIO connected to digital GPIO module, bit set: GPIO connected to analog RTC module) (19 = RTC_IO_TOUCH_PAD13_MUX_SEL_M)
RTC_GPIO_ENABLE_REG = Register(soc.DR_REG_RTCIO_BASE + 0x0C)
RTC_GPIO_ENABLE_REG.set_bit(10 + pin_number) # GPIO shall be output, not input (this also enables a pull-down by default)

# dont need to set wakeup_period for this example
# ulp.set_wakeup_period(0, 50000)
ulp.run(binary, entrypoint=0, pins=[board.IO13])
