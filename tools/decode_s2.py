import esp32_ulp.opcodes_s2 as opcodes


alu_cnt_ops = ('STAGE_INC', 'STAGE_DEC', 'STAGE_RST')
alu_ops = ('ADD', 'SUB', 'AND', 'OR', 'MOVE', 'LSH', 'RSH')
jump_types = ('--', 'EQ', 'OV')
cmp_ops = ('LT', 'GT', 'EQ')
bs_cmp_ops = ('??', 'LT', '??', 'GT', 'EQ', 'LE', '??', 'GE')

lookup = {
    opcodes.OPCODE_ADC: ('ADC', opcodes._adc, lambda op: 'ADC r%s, %s, %s' % (op.dreg, op.mux, op.sar_sel)),
    opcodes.OPCODE_ALU: ('ALU', opcodes._alu_imm, {
        opcodes.SUB_OPCODE_ALU_CNT: (
            'ALU_CNT',
            opcodes._alu_cnt,
            lambda op: '%s%s' % (alu_cnt_ops[op.sel], '' if op.sel == opcodes.ALU_SEL_STAGE_RST else ' %s' % op.imm)
        ),
        opcodes.SUB_OPCODE_ALU_IMM: (
            'ALU_IMM',
            opcodes._alu_imm,
            lambda op: '%s r%s, %s' % (alu_ops[op.sel], op.dreg, op.imm) if op.sel == opcodes.ALU_SEL_MOV
                else '%s r%s, r%s, %s' % (alu_ops[op.sel], op.dreg, op.sreg, op.imm)
        ),
        opcodes.SUB_OPCODE_ALU_REG: (
            'ALU_REG',
            opcodes._alu_reg,
            lambda op: '%s r%s, r%s' % (alu_ops[op.sel], op.dreg, op.sreg) if op.sel == opcodes.ALU_SEL_MOV
                else '%s r%s, r%s, r%s' % (alu_ops[op.sel], op.dreg, op.sreg, op.treg)
        ),
    }),
    opcodes.OPCODE_BRANCH: ('BRANCH', opcodes._bx, {
        opcodes.SUB_OPCODE_BX: (
            'BX',
            opcodes._bx,
            lambda op: 'JUMP %s%s' % (op.addr if op.reg == 0 else 'r%s' % op.dreg, ', %s' % jump_types[op.type]
                if op.type != 0 else '')
        ),
        opcodes.SUB_OPCODE_B: (
            'BR',
            opcodes._b,
            lambda op: 'JUMPR %s, %s, %s' % ('%s%s' % ('-' if op.sign == 1 else '', op.offset), op.imm, cmp_ops[op.cmp])
        ),
        opcodes.SUB_OPCODE_BS: (
            'BS',
            opcodes._bs,
            lambda op: 'JUMPS %s, %s, %s' % ('%s%s' % ('-' if op.sign == 1 else '', op.offset), op.imm, bs_cmp_ops[op.cmp])
        ),
    }),
    opcodes.OPCODE_DELAY: (
        'DELAY',
        opcodes._delay,
        lambda op: 'NOP' if op.cycles == 0 else 'WAIT %s' % op.cycles
    ),
    opcodes.OPCODE_END: ('END', opcodes._end, {
        opcodes.SUB_OPCODE_END: (
            'WAKE',
            opcodes._end
        ),
    }),
    opcodes.OPCODE_HALT: ('HALT', opcodes._halt),
    opcodes.OPCODE_I2C: (
        'I2C',
        opcodes._i2c,
        lambda op: 'I2C_%s %s, %s, %s, %s' % ('RD' if op.rw == 0 else 'WR', op.sub_addr, op.high, op.low, op.i2c_sel)
    ),
    opcodes.OPCODE_LD: (
        'LD/LDH',
        opcodes._ld,
        lambda op: '%s r%s, r%s, %s' % ('LDH' if op.rd_upper else 'LD', op.dreg, op.sreg, twos_comp(op.offset, 11))
    ),
    opcodes.OPCODE_ST: ('ST', opcodes._st, {
        opcodes.SUB_OPCODE_ST_AUTO: (
            'STI/STI32',
            opcodes._st,
            lambda op: 'STI32 r%s, r%s, %s' % (op.sreg, op.dreg, op.label) if op.wr_way == 0
                else 'STI r%s, r%s, %s' % (op.sreg, op.dreg, op.label) if op.label
                else 'STI r%s, r%s' % (op.sreg, op.dreg)
        ),
        opcodes.SUB_OPCODE_ST_OFFSET: (
            'STO',
            opcodes._st,
            lambda op: 'STO %s' % twos_comp(op.offset, 11)
        ),
        opcodes.SUB_OPCODE_ST: (
            'ST/STH/ST32',
            opcodes._st,
            lambda op: '%s r%s, r%s, %s, %s' % ('STH' if op.upper else 'STL', op.sreg, op.dreg, twos_comp(op.offset, 11), op.label) if op.wr_way and op.label
                else '%s r%s, r%s, %s' % ('STH' if op.upper else 'ST', op.sreg, op.dreg, twos_comp(op.offset, 11)) if op.wr_way
                else 'ST32 r%s, r%s, %s, %s' % (op.sreg, op.dreg, twos_comp(op.offset, 11), op.label)
        )
    }),
    opcodes.OPCODE_RD_REG: (
        'RD_REG',
        opcodes._rd_reg,
        lambda op: 'REG_RD 0x%x, %s, %s' % (op.periph_sel << 8 | op.addr, op.high, op.low)
    ),
    opcodes.OPCODE_WR_REG: (
        'WR_REG',
        opcodes._wr_reg,
        lambda op: 'REG_WR 0x%x, %s, %s, %s' % (op.periph_sel << 8 | op.addr, op.high, op.low, op.data)
    ),
    opcodes.OPCODE_TSENS: ('TSENS', opcodes._tsens, lambda op: 'TSENS r%s, %s' % (op.dreg, op.delay)),
}


def twos_comp(val, bits):
    """
    compute the correct value of a 2's complement
    based on the number of bits in the source
    """
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)         # compute negative value
    return val


def decode_instruction(i):
    if i == 0:
        raise Exception('<empty>')

    ins = opcodes._end
    ins.all = i  # abuse a struct to get opcode

    params = lookup.get(ins.opcode, None)

    if not params:
        raise Exception('Unknown instruction')

    if len(params) == 3:
        name, ins, third = params
        ins.all = i

        if callable(third):
            params = (third(ins), ins)
        else:
            params = third.get(ins.sub_opcode, ())

    if len(params) == 3:
        name, ins, pretty = params
        ins.all = i
        name = pretty(ins)
    else:
        name, ins = params
        ins.all = i

    return ins, name


def get_instruction_fields(ins):
    possible_fields = (
        'addr', 'cmp', 'cycle_sel', 'cycles', 'data', 'delay', 'dreg',
        'high', 'i2c_sel', 'imm', 'low', 'mux', 'offset', 'opcode',
        'periph_sel', 'reg', 'rw', 'sar_sel', 'sel', 'sign', 'sreg',
        'sub_addr', 'sub_opcode', 'treg', 'type', 'unused', 'unused1',
        'unused2', 'wakeup',
        'rd_upper', 'label', 'upper', 'wr_way',
    )
    field_details = []
    for field in possible_fields:
        extra = ''
        try:
            # eval is ugly but constrained to possible_fields and variable ins
            val = eval('i.%s' % field, {}, {'i': ins})
            if (val>9):
                extra = ' (0x%02x)' % val
        except KeyError:
            continue

        if field == 'sel':  # ALU
            if ins.sub_opcode == opcodes.SUB_OPCODE_ALU_CNT:
                extra = ' (%s)' % alu_cnt_ops[val]
            else:
                extra = ' (%s)' % alu_ops[val]
        elif field == 'type':  # JUMP
            extra = ' (%s)' % jump_types[val]
        elif field == 'cmp':  # JUMPR/JUMPS
            if ins.sub_opcode == opcodes.SUB_OPCODE_BS:
                extra = ' (%s)' % bs_cmp_ops[val]
            else:
                extra = ' (%s)' % cmp_ops[val]
        elif field == 'offset':
            if ins.opcode in (opcodes.OPCODE_ST, opcodes.OPCODE_LD):
                val = twos_comp(val, 11)

        field_details.append((field, val, extra))

    return field_details
