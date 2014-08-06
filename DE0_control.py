from ftdi import list_devices, setvidpid
from sld_controller import SLD_Controller
from bitstring import BitArray
import sys
import subprocess
from time import sleep


def main():
    if sys.platform == 'darwin' or sys.platform == 'linux2':
        setvidpid(0x09fb, 0x6001) # make DE0 known by ftd2xx library
    devs=list_devices()
    print 'detected devices', devs # make sure the device is detected
    if not devs:
        return

    print 'Killing broken jtagd ...'
    command_line = 'killall jtagd'
    r = subprocess.call(command_line, shell=True)
    print 'return code:', r

    print 'Programming ...'
    command_line = 'quartus_pgm -c \'USB-Blaster\' -m JTAG -o \'p;InitialTest.sof\''
    r = subprocess.call(command_line, shell=True)
    print 'return code:', r

    sld = SLD_Controller('USB-Blaster', 4, 1)

    sld.TAP_Reset()

    d = 0
    a = 0
    b = 0
    sld.VIR_Write(1, BitArray('0b10001'))

    options = {0 : 0x08,
               1 : 0x14,
               2 : 0x22,
               3 : 0x41,
               4 : 0x22,
               5 : 0x14,
    }

    while b < 50:

        read_back = sld.VDR_Write_Read(BitArray(uint=d, length=7))
        print read_back.bin

        sleep(0.15)

        d = options[a]

        if a == 5:
            a = 0
            b += 1
            continue

        a += 1

    sld.VIR_Write(1, BitArray('0b10000'))
    sld.TAP_Reset()
    sld.close()

if __name__ == '__main__':
    main()
