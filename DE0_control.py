from ftdi import list_devices, setvidpid
from sld_controller import SLD_Controller
from bitstring import BitArray
import sys


def main():
    if sys.platform == 'darwin':
        setvidpid(0x09fb, 0x6001) # make DE0 known by ftd2xx library
    devs=list_devices()
    print 'detected devices', devs # make sure the device is detected
    if not devs:
        return

    sld = SLD_Controller('USB-Blaster', 4, 1)

    # sld.TAP_Reset()

    print sld.VDR_Write_Read(BitArray('0b1010101'))
    sld.close()

if __name__ == '__main__':
    main()