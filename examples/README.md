These examples require [my branch](https://github.com/Sola85/circuitpython/tree/improve_espulp) of circuitpython to work.

They are tested on an esp32s3. 

`main_counter.py` should work on an esp32s2 without any changes and should work on an esp32 by simply changing the target cpu in the call to `src_to_binary`. 

All other examples require the addresses of registers to be adjusted in the main python files, as indicated by the comments in the appropriate places.

`main_counter_precompiled_esp32.py` and `main_counter_precompiled.py` contain precompiled ulp binaries for the counter example that do not require assembling.