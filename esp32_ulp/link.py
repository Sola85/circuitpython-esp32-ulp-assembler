#
# This file is part of the micropython-esp32-ulp project,
# https://github.com/micropython/micropython-esp32-ulp
#
# SPDX-FileCopyrightText: 2018-2023, the micropython-esp32-ulp authors, see AUTHORS file.
# SPDX-License-Identifier: MIT

#from uctypes import struct, addressof, LITTLE_ENDIAN, UINT16, UINT32
import struct

def make_binary(text, data, bss_size):
    if not isinstance(text, bytes):
        raise TypeError('text section must be binary bytes')
    if not isinstance(data, bytes):
        raise TypeError('data section must be binary bytes')
    
    text = text[4:]
    
    format_str = "<IHHHH" # little-endian, uint, ushort*4
    header = struct.pack(format_str, 
                    0x00706c75,
                    12,
                    len(text),
                    len(data),
                    bss_size)
    print("Header:", header)
    print("Text:", text)
    print("Data:", data)
    return header + text + data

    # binary_header_struct_def = dict(
    #     magic = 0 | UINT32,
    #     text_offset = 4 | UINT16,
    #     text_size = 6 | UINT16,
    #     data_size = 8 | UINT16,
    #     bss_size = 10 | UINT16,
    # )
    # header = bytearray(12)
    # h = struct(addressof(header), binary_header_struct_def, LITTLE_ENDIAN)
    # # https://github.com/espressif/esp-idf/blob/master/components/ulp/ld/esp32.ulp.ld
    # # ULP program binary should have the following format (all values little-endian):
    # h.magic = 0x00706c75  # (4 bytes)
    # h.text_offset = 12  # offset of .text section from binary start (2 bytes)
    # h.text_size = len(text)  # size of .text section (2 bytes)
    # h.data_size = len(data)  # size of .data section (2 bytes)
    # h.bss_size = bss_size  # size of .bss section (2 bytes)
    # return bytes(header) + text + data

