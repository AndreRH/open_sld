from ftdi import list_devices, setvidpid
from sld_controller import SLD_Controller
from bitstring import BitArray
import sys
from time import sleep


def main():
    if sys.platform == 'darwin' or sys.platform == 'linux2':
        setvidpid(0x09fb, 0x6001) # make DE0 known by ftd2xx library
    devs=list_devices()
    print 'detected devices', devs # make sure the device is detected
    if not devs:
        return

    sld = SLD_Controller('USB-Blaster', 4, 1)

    sld.TAP_Reset()


    sld.VIR_Write(1, BitArray('0b10001'))

    sld.VDR_Write(BitArray('0b0000001'))
    sleep(.3)
    sld.VDR_Write(BitArray('0b0000010'))
    sleep(.3)
    sld.VDR_Write(BitArray('0b0000100'))
    sleep(.3)
    sld.VDR_Write(BitArray('0b0001000'))
    sleep(.3)

    sld.VIR_Write(1, BitArray('0b10000'))

    sld.close()

if __name__ == '__main__':
    main()
