from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import json
import os
from pathlib import Path
import serial
import threading
import time
import queue

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# GLOBAL VARS
# ------------
#
# Data recording thread
DATARECTHREAD = None

## Experimental Data Recording Endpoints

# Get a list of appropriate serial ports
@app.route('/ports', methods=['GET', 'POST'])
def ports():
    """
    Handle a ports request.
    :return:
    """
    # Use a closure to filter out devices
    def filter_dev(dev_: str):
        dev = dev_.lower()
        if ('cu' in dev) or ('usb' in dev):
            return True
        else:
            return False

    devs = os.listdir('/dev')
    filtered_devs = ['/dev/'+d for d in devs if filter_dev(d)]

    response = jsonify({'ports': filtered_devs})
    # response.headers.add('Access-Control-Allow-Origin', '*')

    return response

# Get a list of appropriate serial ports
@app.route('/start_data_record', methods=['GET'])
def start_data_record():
    """
    Start a serial data recording thread.
    :return:
    """
    global DATARECTHREAD

    args = request.args

    patient_code = args.get('patient')
    session_code = args.get('session')
    record_code = args.get('record')

    HOMEDIR = Path.home()
    logfilename = HOMEDIR / 'EXPDATA' / 'sub_{}'.format(patient_code) / \
                            'sess_{}'.format(session_code) / 'rec_{}.csv'.format(record_code)

    if DATARECTHREAD == None or not DATARECTHREAD.is_alive():
        DATARECTHREAD = SerialDataRecorder(port='/dev/cu.usbmodem14301', baud=115200,
                                           logfile=logfilename)
        DATARECTHREAD.start()
        return "Thread started!".format(patient_code, session_code, record_code)
    else:
        return "Thread is already running!"


@app.route('/stop_data_record', methods=['GET'])
def stop_data_record():
    """
    Stop the running data record thread.
    :return:
    """
    global DATARECTHREAD

    if DATARECTHREAD == None:
        return "No thread running."
    else:
        if DATARECTHREAD.is_alive():
            DATARECTHREAD.stop_recording()
            return "Thread stopped"
        else:
            DATARECTHREAD = None
            return "Thread is already stopped."


class SerialDataRecorder(threading.Thread):
    def __init__(self, port, baud, logfile=Path('log.txt')):
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

        # Create the logfile directory if it does not exist.
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
    app.run()