import threading
import serial
import queue
import time

class SerialDataRecorder(threading.Thread):
    def __init__(self, port, baud, logfile='log.txt'):
        super(SerialDataRecorder, self).__init__()
        self.port = port
        self.baud = baud
        self.logfile = logfile
        # Serial port object
        self.spobj = None
        # Message queue
        self.msgq = queue.Queue()
        # Set up as a daemon thread so that it exits when the main program exits.
        self.daemon = True

    def run(self):
        """
        Main thread function
        :return:
        """
        # Initialize the serial port
        self.spobj = serial.Serial(self.port, self.baud)

        # Start an infinite loop
        MSG = None
        BYTES = 0
        with open(self.logfile, 'w') as fp:
            while True:
                time.sleep(0.1)

                if self.spobj.inWaiting() > 0:
                    serial_data = self.spobj.read(self.spobj.inWaiting())
                    serial_str = serial_data.decode('utf-8')
                    fp.write(serial_str)
                    BYTES += len(serial_data)

                try:
                    MSG = self.msgq.get(False)

                    if MSG == 'STOP':
                        break
                except queue.Empty:
                    pass

        # Thread is winding down.
        print("Serial thread is exiting...")
        print("{} bytes logged".format(BYTES))
        self.spobj.close()
        return BYTES

    def stop_recording(self):
        """
        Tell the serial thread to stop.
        :return:
        """
        self.msgq.put('STOP')

if __name__ == '__main__':
    t = SerialDataRecorder(port='/dev/cu.usbmodem14301', baud=115200)
    t.start()

    time.sleep(5)
    t.stop_recording()
    t.join()
