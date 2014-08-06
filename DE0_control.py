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

    while True:

        read_back = sld.VDR_Write_Read(BitArray(uint=d, length=7))
        print read_back.bin

        if a == 0:
            d = 8
        elif a == 1:
            d = 20
        elif a == 2:
            d = 34
        elif a == 3:
            d = 65
        elif a == 4:
            d = 34
        else:
            d = 20

        if b == 50:
            break

        if a == 5:
            a = 0
            b += 1
            continue

        a += 1

        sleep(0.15)

    sld.VIR_Write(1, BitArray('0b10000'))
    sld.TAP_Reset()
    sld.close()

if __name__ == '__main__':
    main()
