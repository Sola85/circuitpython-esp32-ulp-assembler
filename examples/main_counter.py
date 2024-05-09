"""
A simple example demonstrating how the main cpu can access variables on the ULP.
The ULP increments a variable once per second and the main cpu prints this variable.
"""

from esp32_ulp import src_to_binary
import espulp
import memorymap
from time import sleep


source = """
data:       .long 123          # initial value of data variable

entry:      move r3, data    # load address of data into r3
            ld r2, r3, 0     # load data contents ([r3+0]) into r2
            add r2, r2, 1    # increment r2
            st r2, r3, 0     # store r2 contents into data ([r3+0])

            halt             # halt ULP co-prozessor (until it gets waked up again)
"""


binary = src_to_binary(source, cpu="esp32s2")  # cpu is esp32 or esp32s2

ulp = espulp.ULP()
ulp.halt()
ulp.set_wakeup_period(0, 1000000) # 1 million micro seconds = wake up once per second
ulp.run(binary, entrypoint=4)


data_variable = memorymap.AddressRange(start=0x50000000, length=4)

while True:
    print(int.from_bytes(data_variable[:], "little"))
    sleep(1)
