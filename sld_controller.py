import ctypes as c
from bitstring import BitArray
from ftdi import open_ex_by_name


#------------------------------------------------------------------------------
#
# Create a write buffer as a ctypes array of bytes

def tx_buffer(byte_list):
    return (c.c_ubyte * len(byte_list))(*byte_list)

#-------------------------------------------------------------------------------
#
# FT245 Bit definitions for JTAG mode

OFF = 0x00
TCK = 0x01
TMS = 0x02
TDI = 0x10
LED = 0x20
RD  = 0x40
sHM = 0x80

# Bit-mode - Two byte codes
M0D0R = [LED             | RD , LED             | TCK]
M0D1R = [LED | TDI       | RD , LED       | TDI | TCK]
M1D0R = [LED | TMS       | RD , LED | TMS | TCK]
M1D1R = [LED | TMS | TDI | RD , LED | TMS | TDI | TCK]

M0D0 = [LED                   , LED             | TCK]
M0D1 = [LED | TDI             , LED       | TDI | TCK]
M1D0 = [LED | TMS             , LED | TMS       | TCK]
M1D1 = [LED | TMS | TDI       , LED | TMS | TDI | TCK]

# TAP controller Reset
TAP_RESET = tx_buffer(M1D0 + M1D0 + M1D0 + M1D0 + M1D0)

# TAP controller Reset to Idle
TAP_IDLE = tx_buffer(M0D0)

# TAP controller Idle to Shift_DR
TAP_SHIFT_DR = tx_buffer(M1D0 + M0D0 + M0D0)

# TAP controller Idle to Shift_IR
TAP_SHIFT_IR = tx_buffer(M1D0 + M1D0 + M0D0 + M0D0)

# TAP controller Exit1 to Idle
TAP_END_SHIFT = tx_buffer(M1D0 + M0D0)

# IR values

SELECT_VIR = tx_buffer(M0D0 + M0D1 + M0D1 + M0D1 + M0D0 +
                       M0D0 + M0D0 + M0D0 + M0D0 + M1D0)

SELECT_VDR = tx_buffer(M0D0 + M0D0 + M0D1 + M0D1 + M0D0 +
                       M0D0 + M0D0 + M0D0 + M0D0 + M1D0)

NODE_SHIFT_INST  = tx_buffer(M0D1 + M0D0 + M0D0 + M0D0 + M1D1)

NODE_UPDATE_INST = tx_buffer(M0D0 + M0D0 + M0D0 + M0D0 + M1D1)

# Node Data
NODE_DATA = tx_buffer(M0D0 + M0D1 + M0D1 + M0D0 + M0D0 + M0D1 + M1D1)

#------------------------------------------------------------------------------
#
# Create an iterator returning 1/0 from bytes read from the FT245

def rx_bits(byte_list):
    for c in byte_list[::-1]:
        yield ord(c) & 1

#------------------------------------------------------------------------------
#
# Decode a list of FT245 command bytes

def decoded(cmd):
    i = 0
    result = []
    while True:
        b2 = [cmd[i], cmd[i+1]]
        if   b2 == M0D0R:
            result.append('M0D0R')
        elif b2 == M0D1R:
            result.append('M0D1R')
        elif b2 == M1D0R:
            result.append('M1D0R')
        elif b2 == M1D1R:
            result.append('M1D1R')

        elif b2 == M0D0:
            result.append('M0D0')
        elif b2 == M0D1:
            result.append('M0D1')
        elif b2 == M1D0:
            result.append('M1D0')
        elif b2 == M1D1:
            result.append('M1D1')

        i += 2
        if i == len(cmd):
            break

    return ','.join(result)



class SLD_Controller(object):

    def __init__(self, interface_name, m_width, n_width, csv_file_name = ''):

        self.interface = open_ex_by_name(interface_name)

        self.instruction_width  = 10
        self.virtual_inst_width = m_width
        self.node_adrs_width    = n_width

        self.interface.reset_device()
        self.interface.write(TAP_RESET)
        self.interface.write(TAP_IDLE)

    #----

    def TAP_Reset(self):
        self.interface.write(TAP_RESET)
        self.interface.write(TAP_IDLE)

    #----

    def IR_Write(self, instruction):
        self.interface.write(TAP_SHIFT_IR)
        self.interface.write(dataBuffer(instruction))
        self.interface.write(TAP_END_SHIFT)

    #----

    def VIR_Write(self, node, instruction):

        #  load the JTAG IR with USER1 to select the Virtual IR
        self.interface.write(TAP_SHIFT_IR)
        self.interface.write(dataBuffer(BitArray('0b0000001110')))
        self.interface.write(TAP_END_SHIFT)

        # Load node 1 virtual IR with SHIFT instruction
        self.interface.write(TAP_SHIFT_DR)
        self.interface.write(dataBuffer(instruction))
        self.interface.write(TAP_END_SHIFT)

    #----

    def VDR_Read(self, size):
        return self.VDR_Write_Read(BitArray(size))

    #----

    def VDR_Write(self, data):

        #  load the JTAG IR with USER0 to select the Virtual DR
        self.interface.write(TAP_SHIFT_IR)
        self.interface.write(dataBuffer(BitArray('0b0000001100')))
        self.interface.write(TAP_END_SHIFT)

        # Load node 1 virtual DR with data
        self.interface.write(TAP_SHIFT_DR)
        self.interface.write(dataBuffer(data))
        self.interface.write(TAP_END_SHIFT)

    #----

    def VDR_Write_Read(self, data):

        #  load the JTAG IR with USER0 to select the Virtual DR
        self.interface.write(TAP_SHIFT_IR)
        self.interface.write(dataBuffer(BitArray('0b0000001100')))
        self.interface.write(TAP_END_SHIFT)

        # Load node 1 virtual DR with data
        self.interface.write(TAP_SHIFT_DR)
        self.interface.write(dataBuffer(data, True))
        self.interface.write(TAP_END_SHIFT)

        # Wait for the read data
        size = len(data)
        while True:
            count = self.interface.get_queue_status()
            if count == size:
                break

        # Get the read data, converting it to a BitArray
        return BitArray(rx_bits(self.interface.read(count, True)))

    #----

    def close(self):
        self.interface.close()



#-------------------------------------------------------------------------------
#
# Create a ctypes array of bytes from a BitArray (bits) instance

def dataBuffer(bits, rd=False):

    # Get the bits in LSB first order
    bits.reverse()
    data_bytes = []

    if rd:
        # Read back data on TDO
        # Process all but the MSB
        for b in bits[:-1]:
            if b:
                data_bytes += M0D1R
            else:
                data_bytes += M0D0R

        # Process MSB
        if bits[-1]:
            data_bytes += M1D1R
        else:
            data_bytes += M1D0R

    else:
        # Don't read back data on TDO
        # Process all but the MSB
        for b in bits[:-1]:
            if b:
                data_bytes += M0D1
            else:
                data_bytes += M0D0

        # Process MSB
        if bits[-1]:
            data_bytes += M1D1
        else:
            data_bytes += M1D0

#     print 'dataBuffer %s' % decoded(data_bytes)

    return tx_buffer(data_bytes)
