import threading
import serial
import queue
import time
from pathlib import Path

# DEFAULT_CONFIG = {"serial":
#                       {"port": '/dev/cu.usbmodem14401',
#                        "baud": 115200},
#                   "control":
#                       {"pid":
#                            {"Kp": 0.5,
#                             "Ki": 0.0,
#                             "Kd": 0.5},
#                        "assistance":
#                            {"Swing Period Est1": 0.5,
#                             "Rising Ratio": 0.5,
#                             "PreSwing Period": 0.5,
#                             "PFAssist Level": 0.5,
#                             "DF Assist Level": 0.5}}}

DEFAULT_SERIAL_SETTINGS = {"port": '/dev/ttyS0',
                           "baud": 500000}
DEFAULT_CONTROL_SETTINGS = [
    {"name": "Kp",
     "value": 0.5,
     "help": "PID Controller Proportional Gain"},
    {"name": "Ki",
     "value": 0.5,
     "help": "PID Controller Integral Gain"},
    {"name": "Kd",
     "value": 0.5,
     "help": "PID Controller Derivative Gain"}
]

DEFAULT_ASSIST_SETTINGS = [
    {"name": "Swing Period Est1",
     "value": 0.5,
     "units": "s",
     "help": "Estimate of the swing period"},
    {"name": "Rising Ratio",
     "value": 0.5,
     "units": "-",
     "help": ""},
    {"name": "PreSwing Period",
     "value": 0.3,
     "units": "s",
     "help": "Estimation of Pre-swing period"},
    {"name": "PF Assist Level",
     "value": 0.5,
     "units": "ratio",
     "help": "the ratio to 500N magnitude"},
    {"name": "DF Assist Level",
     "value": 0.5,
     "units": "ratio",
     "help": "the ratio to 100N magnitude"}
]



DEFAULT_CONFIG = {"serial": DEFAULT_SERIAL_SETTINGS,
                  "control": DEFAULT_CONTROL_SETTINGS,
                  "assistance": DEFAULT_ASSIST_SETTINGS
                  }


class SerialDataRecorder(threading.Thread):
    def __init__(self, port, baud,
                 logfile=Path('log.txt'),
                 patient=1,
                 session=1,
                 record=1):
        super(SerialDataRecorder, self).__init__()
        self.port = port
        self.baud = baud
        self.logfile = logfile
        self.patient = patient
        self.session = session
        self.record = record
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
        # Create file if it does not exist.
        self.logfile.parent.mkdir(parents=True, exist_ok=True)

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
                    fp.flush()
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
    t = SerialDataRecorder(port=DEFAULT_SERIAL_SETTINGS['port'], baud=DEFAULT_SERIAL_SETTINGS['baud'])
    t.start()

    time.sleep(5)
    t.stop_recording()
    t.join()
