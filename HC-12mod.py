#!/usr/bin/env python3
 
import serial
import time
import RPi.GPIO as GPIO
import logging

logger = logging.getLogger("hydrosys4."+__name__)
 

class _SerialConnection:

    def __init__(self, port="/dev/serial0",baudrate=9600,timeout=1):
        self.port=port
        self.baudrate=baudrate
        self.timeout=timeout
        self.ser=self.setserial()
        self.listen=False
        self.received_data=""

    def setserial(self):
        ser = serial.Serial(port=self.port,baudrate=self.baudrate,timeout=self.timeout) # timeout is in seconds
        time.sleep(1)
        ser.flushInput()
        return ser

    def listenSerial(self):
        print("Listening Serial Port")
        self.ser.flushInput()
        while self.listen:
            isok , received_data = self.readSerialBuffer()
            if isok and received_data:
                print (received_data)
                self.received_data=received_data
            time.sleep(0.2)
    
    def close(self):
        self.ser.close()

    def restart(self):
        logger.warning("Try to Restart Serial Connection")
        print("Try to Restart Serial")
        self.ser.close()
        self.ser.open()
        time.sleep(1)

    def readSerialBuffer(self):
        ser=self.ser
        received_data=""
        try:        
            size = ser.inWaiting()
            if size > 0:
                # wait to see if the buffer increments
                time.sleep(0.5)
                size = ser.inWaiting()
                received_data = ser.read(size).decode("ascii")
        except IOError:
            self.restart()
            return False, received_data
        return True, received_data

    def sendString(self,stringdata):
        self.ser.write(bytes((stringdata+"\n"), 'utf-8'))

class HC12:

    def __init__(self, ATcommandslist):
        if ATcommandslist:
            self.ATcommandslist=ATcommandslist
        else:
            self.ATcommandslist=["AT+DEFAULT\n","AT+P4\n","AT+C001\n"]

        # define the Set PIN
        self.SetPIN=4
        # start serial connection    
        self.ser=_SerialConnection()
        if self.VerifySerialAT:
            print("HC-12 active check: OK")
            logger.info("HC-12 active check: OK")
            isok = self.setATcommands()
            if isok:
                print("AT Commands settong: OK")
                logger.info("AT Commands settong: OK")
            else:
                print("AT Commands settong: Problems detected")
                logger.warning("AT Commands settong: Problems detected")
            # init serial reading cycle
            self.ser.listen=True
            self.ser.listenSerial()


    def VerifySerialAT(self):
        ser=self.ser
        isok=False
        #send first AT command just to check the HC-12 is answering
        print("Check if AT commnds are working")
        cmd="AT\n"
        outok , received_data = self.sendReceiveATcmds(cmd)

        if "ok" in received_data or "OK" in received_data:
            isok=True
            print ("Check AT Successfull")
        return isok
 
    def sendReceiveATcmds(self,cmd):
        ser=self.ser
        isok=False
        print("send AT command = ", cmd)
        ser.sendString(cmd)
        j=0
        received_data=""   
        while (j<5):
            time.sleep(0.5)
            outok, received_data = ser.readSerialBuffer()   
            if outok:
                if received_data:
                    print("Received = " , received_data)
                    isok=True
                    break
                else:
                    # try to send again the comamand
                    print("re-send AT command = ", cmd)
                    ser.sendString(cmd)
            print(j, "inside loop Command =",cmd)
            j=j+1
        return isok , received_data

    def setATcommands(self):
        # the HC-12 set pin should be put to LOW to enable AT commands
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SetPIN, GPIO.OUT, initial=GPIO.LOW) # set pin 7 (GPIO4) to OUTPUT (SET pin of HC12)
        GPIO.output(self.SetPIN, GPIO.LOW) # set HC12 to AT mode

        ATok = self.VerifySerialAT()

        if ATok:
            for cmd in ATcommandslist:
                isok , received_data = self.sendReceiveATcmds(cmd)
                if not isok:
                    print("Warning , No response for AT command = ", cmd)

        GPIO.output(self.SetPIN, GPIO.HIGH) # set HC12 to normal mode
        time.sleep(0.5)

        return ATok





	
if __name__ == '__main__':
    
    ATcommandslist=["AT+DEFAULT\n","AT+P4\n","AT+C001\n"]
    HC12(ATcommandslist)


    """
    AT+Cxxx: Change wireless communication channel, selectable from 001 to 127 (for wireless channels exceeding 100, the communication distance cannot be guaranteed). The default value for the wireless channel is 001, with a working frequency of 433.4MHz. The channel stepping is 400KHz, and the working frequency of channel 

    AT+FUx:  Change the serial port transparent transmission mode of the module. Four modes are available, namely FU1, FU2, FU3, and FU4. Only when the serial port speed, channel, and transparent transmission mode of two modules is set to be the same,can normal wireless communications occur. For more details, please see the abovesection “Wireless Serial Port Transparent Transmission”.
    FU4 mode is useful for maximum range, up to 1.8km. Only a single baud rate of 1200bps is supported, with the in the air baud rate reduced to 500bps for improved communication distance. This mode can only be used for small amounts ofdata (each packet should be 60 bytes or less), and the time interval between sending packets must not be too short (preferably no less than 2 seconds) in order to prevent loss of data.

    AT+Px:   Set the transmitting power of the module, with x selectable from 1 to 8, default 8.
    
    """ 


