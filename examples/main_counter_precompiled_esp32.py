"""
The compiled version of the counter example, containing the compiled binary for the ESPS2/S3.
"""

import espulp
import memorymap
from time import sleep

binary = b'ulp\x00\x0c\x00\x18\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x80r\x0e\x00\x00\xd0\x1a\x00\x00r\x0e\x00\x00h\x00\x00\x00\xb0'

ulp = espulp.ULP()
ulp.halt()
ulp.set_wakeup_period(0, 1000000) # 1 million micro seconds = wake up once per second
ulp.run(binary, entrypoint=4)


data_variable = memorymap.AddressRange(start=0x50000000, length=2)

while True:
    print(int.from_bytes(data_variable[:], "little"))
    sleep(1)
