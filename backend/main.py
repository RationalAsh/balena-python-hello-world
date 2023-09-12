import time

from flask import Flask, jsonify, request, flash, redirect, url_for
from flask_cors import CORS, cross_origin
import json
import os
from pathlib import Path
import sys
sys.path.append("/home/pi/Documents/exo_gui_flask_v2")
import utils
import toml
from werkzeug.utils import secure_filename
import subprocess
import logging
import string
import pandas as pd

# GLOBAL VARS
# ------------
#

logging.getLogger('flask_cors').level = logging.DEBUG

# Data recording thread
DATARECTHREAD = None

# Specify the working directory
# If we're on macos, use the Home directory
if sys.platform == 'darwin':
    WORKINGDIR = Path.home()
else:
    WORKINGDIR = Path('/data')

# Path to configuration file.
CONFIGPATH = WORKINGDIR / '.exoskeleton' / 'config.toml'

# Path to the location of binary firmware file for programming micro-controller.
FIRMWAREPATH = WORKINGDIR / '.exoskeleton' / 'firmware.bin'
ALLOWED_EXTENSIONS = {'bin'}


# Set up the app.
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['FIRMWARE-PATH'] = FIRMWAREPATH
app.config['UPLOAD_FOLDER'] = FIRMWAREPATH.parent
app.config['PYSTLINK'] = Path.home() / 'Documents' / 'pystlink' / 'pystlink.py'
app.config['DATAPATH'] = WORKINGDIR


# Endpoints to handle settings and other parameters
@app.route('/settings/serial', methods=['GET', 'POST'])
def settings_serial():
    """
    Get serial port settings
    :return:
    """
    if request.method == 'GET':
        with open(CONFIGPATH, 'r') as fp:
            settings_dict = toml.load(fp)

        response = {'endpoint': request.path,
                    'response': settings_dict['serial']}

        return jsonify(response)
    elif request.method == 'POST':
        with open(CONFIGPATH, 'r') as fp:
            current_settings = toml.load(fp)

        request_data = request.get_json()

        port = request_data.get('port')
        baud = request_data.get('baud')

        if request_data:
            if port:
                current_settings['serial']['port'] = port
            if baud:
                current_settings['serial']['baud'] = baud

            with open(CONFIGPATH, 'w') as fp:
                toml.dump(current_settings, fp)
        else:
            pass

        response = {'endpoint': request.path,
                    'response': current_settings['serial']}

        return jsonify(response)


@app.route('/settings/control', methods=['GET', 'POST'])
def settings_control():
    """
    Get control parameter settings
    :return:
    """
    if request.method == 'GET':
        with open(CONFIGPATH, 'r') as fp:
            settings_dict = toml.load(fp)
        response = {'endpoint': request.path,
                    'response': settings_dict['control']}
        return jsonify(response)
    elif request.method == 'POST':
        with open(CONFIGPATH, 'r') as fp:
            current_settings = toml.load(fp)

        request_data = request.get_json()
        if request_data:
            current_settings['control'] = request_data

            with open(CONFIGPATH, 'w') as fp:
                toml.dump(current_settings, fp)

        else:
            pass

        response = {'endpoint': request.path,
                    'response': current_settings['control']}

        return jsonify(response)

@app.route('/settings/assistance', methods=['GET', 'POST'])
def settings_assistance():
    """
    Get control parameter settings
    :return:
    """
    if request.method == 'GET':
        with open(CONFIGPATH, 'r') as fp:
            settings_dict = toml.load(fp)
        response = {'endpoint': request.path,
                    'response': settings_dict['assistance']}
        return jsonify(response)
    elif request.method == 'POST':
        with open(CONFIGPATH, 'r') as fp:
            current_settings = toml.load(fp)

        request_data = request.get_json()
        if request_data:
            current_settings['assistance'] = request_data

            with open(CONFIGPATH, 'w') as fp:
                toml.dump(current_settings, fp)

        else:
            pass

        response = {'endpoint': request.path,
                    'response': current_settings['assistance']}

        return jsonify(response)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/settings/firmware', methods=['GET', 'POST'])
@cross_origin()
def upload_new_firmware():
    """
    Upload new firmware to the server.
    :return:
    """
    if request.method == 'POST':
        # Check if the post request has the file part.
        if 'file' not in request.files:
            return jsonify({'endpoint': request.path, 'upload': 'FAILED', 'reason': 'NO FILE'})

        file = request.files['file']

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return jsonify({'endpoint': request.path, 'upload': 'FAILED', 'reason': 'FILE EMPTY'})
        if file and allowed_file(file.filename):
            app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)
            filename = secure_filename(file.filename)

            fpath = app.config['UPLOAD_FOLDER']

            # If the file exists delete it.
            #fpath.unlink(missing_ok=True)

            file.save(app.config['UPLOAD_FOLDER'] / 'firmware.bin')
            return jsonify({'endpoint': request.path, 'upload': 'OK'})


@app.route('/microcontroller/info', methods=['GET'])
def microcontroller_info():
    """
    Get information about the micro-controller on board the exoskeleton.
    :return:
    """
    output = subprocess.run(['st-info', '--probe'],
                            capture_output=True)

    all_output = (output.stdout + output.stderr).decode('utf-8')

    if all_output == 'Found 0 stlink programmers':
        return jsonify({'endpoint': request.path, 'error': 'PROGRAMMER DISCONNECTED'})
    else:
        oplines = all_output.split('\n')

        MCU = ''
        infodict = {}
        for l in oplines:
            if ':' in l:
                infodict[l[:l.find(':')].strip()] =  l[l.find(':')+1:].strip()

        return jsonify({'endpoint': request.path, 'info': infodict})


@app.route('/microcontroller/reflash', methods=['POST'])
def reflash_firmware():
    """
    Re-flash firmware of the microcontroller.
    :return:
    """
    firmware_file = app.config['UPLOAD_FOLDER'] / 'firmware.bin'
    # output = subprocess.run(['st-flash', '--connect-under-reset', 'write', str(firmware_file), '0x8000000'],
    #                         capture_output=True)
    output = subprocess.run(['python3',
                             app.config['PYSTLINK'],
                             'flash:erase',
                             'flash:verify:0x8000000:'+str(firmware_file)],
                             capture_output=True)
    all_output = output.stdout + output.stderr

    return jsonify({'endpoint': request.path,
                    'output': all_output.decode('utf-8')})

## Experimental Data Recording Endpoints
# Get a list of appropriate serial ports
@app.route('/utils/ports', methods=['GET'])
def ports():
    """
    Handle a ports request.
    :return:
    """
    # Use a closure to filter out devices
    def filter_dev(dev_: str):
        dev = dev_.lower()
        if ('cu' in dev.lower()) or ('usb' in dev.lower()) or ('acm' in dev.lower()) or ('S0' in dev):
            return True
        else:
            return False

    devs = os.listdir('/dev')
    filtered_devs = ['/dev/'+d for d in devs if filter_dev(d)]

    response = {'response': devs, 'endpoint': request.path}
    # response.headers.add('Access-Control-Allow-Origin', '*')

    return jsonify(response)


# Get a list of appropriate serial ports
@app.route('/record/start', methods=['POST'])
def start_data_record():
    """
    Start a serial data recording thread.
    :return:
    """
    global DATARECTHREAD

    with open(CONFIGPATH, 'r') as fp:
        settings_dict = toml.load(fp)

    args = request.get_json()

    patient_code = args.get('patient')
    session_code = args.get('session')
    record_code = args.get('record')

    HOMEDIR = WORKINGDIR
    logfilename = HOMEDIR / 'EXPDATA' / 'sub_{}'.format(patient_code) / \
                            'sess_{}'.format(session_code) / 'rec_{}.csv'.format(record_code)

    if DATARECTHREAD is None or not DATARECTHREAD.is_alive():
        DATARECTHREAD = utils.SerialDataRecorder(port=settings_dict['serial']['port'],
                                                 baud=settings_dict['serial']['baud'],
                                                 logfile=logfilename,
                                                 patient=patient_code,
                                                 session=session_code,
                                                 record=record_code)
        DATARECTHREAD.start()

        # Wait for a bit
        time.sleep(0.5)
        if DATARECTHREAD.is_alive():
            return jsonify({'endpoint': request.path, 'status': 'RECORDING'})
        else:
            return jsonify({'endpoint': request.path, 'status': 'ERROR'})
    else:
        return jsonify({'endpoint': request.path, 'status': 'RECORDING'})


@app.route('/record/status', methods=['GET'])
def data_record_status():
    """
    Get status of data recording.
    :return:
    """
    global DATARECTHREAD

    def get_plot_data_dict(fname):
        try:
            # Read file as csv and format the data
            df = pd.read_csv(DATARECTHREAD.logfile)

            # Name columns
            df.columns = ['V{}'.format(i) for i in range(df.shape[1])]

            # Append time
            tvals = [float('{:.2f}'.format(i * 0.01)) for i in range(df.shape[0])]
            df['t'] = tvals

            # Get last few samples
            df = df[-1000:-20]

            return df.to_dict(orient='records')
        except:
            return None


    if DATARECTHREAD:
        patdata = {'patient': DATARECTHREAD.patient,
                   'session': DATARECTHREAD.session,
                   'record': DATARECTHREAD.record}

        if DATARECTHREAD.is_alive():
            patdata['plot'] = get_plot_data_dict(DATARECTHREAD.logfile)
            return jsonify({'endpoint': request.path, 'status': 'RECORDING', 'data': patdata})
        else:
            patdata['plot'] = get_plot_data_dict(DATARECTHREAD.logfile)
            return jsonify({'endpoint': request.path, 'status': 'FINISHED', 'data': patdata})
    else:
        return jsonify({'endpoint': request.path, 'status': 'FINISHED', 'data': None})


@app.route('/record/stop', methods=['POST'])
def stop_data_record():
    """
    Stop the running data record thread.
    :return:
    """
    global DATARECTHREAD

    if DATARECTHREAD == None:
        return {'endpoint': request.path, 'status': 'FINISHED'}
    else:
        if DATARECTHREAD.is_alive():
            DATARECTHREAD.stop_recording()
            return jsonify({'endpoint': request.path, 'status': 'FINISHED'})
        else:
            DATARECTHREAD = None
            return jsonify({'endpoint': request.path, 'status': 'FINISHED'})

@app.route('/data/files', methods=['GET'])
def data_files():
    """
    Get list of data files.
    :return:
    """
    # Read the query string with key 'path'
    path = request.args.get('path')

    # If path is None, then use the default path
    if path is None:
        path = WORKINGDIR / 'EXPDATA'
    else:
        path = WORKINGDIR / 'EXPDATA' / path

    # Get list of all files and folders in the path
    lsout = path.glob('*')

    # Loop over the list and create a dictionary of files and folders
    items = []
    for i in lsout:
        fileData = {
            'name': i.parts[-1],
            'id': str(i.parts[-1]),
            'isDir': True if i.is_dir() else False,
            'isHidden': False if i.parts[-1][0] in string.ascii_letters else True,
        }

        items.append(fileData)

    # Create a response dictionary
    response = {'endpoint': request.path,
                'path': str(path),
                'items': items}

    return jsonify(response)

@app.route('/data/subjects', methods=['GET'])
def data_tree():
    """
    List of subjects with recorded data available.

    :return:
    """
    # Get list of all files and folders in the path
    lsout = (WORKINGDIR / 'EXPDATA').glob('*')

    # Get list of all folders
    dirs = [str(i.parts[-1]) for i in lsout if i.is_dir()]

    # Remove folders that do not start with 'sub_'
    dirs = [i for i in dirs if i[:4] == 'sub_']

    return jsonify({'endpoint': request.path, 'response': dirs})


@app.route('/data/sessions', methods=['GET'])
def data_sessions():
    """
    List of sessions for a given subject.
    :return:
    """
    # Read the query string with key subject
    subject = request.args.get('subject')

    # If subject was not specified, return an error message
    if subject is None:
        return jsonify({'endpoint': request.path,
                        'error': 'NO SUBJECT SPECIFIED'})

    # Get list of all files and folders in the path
    lsout = (WORKINGDIR / 'EXPDATA' / subject).glob('*')

    # Get list of all folders
    dirs = [str(i.parts[-1]) for i in lsout if i.is_dir()]

    # Remove folders that do not start with 'sess_'
    dirs = [i for i in dirs if i[:5] == 'sess_']

    return jsonify({'endpoint': request.path, 'response': dirs})

@app.route('/data/records', methods=['GET'])
def data_records():
    """
    List of records for a given subject and session.
    :return:
    """
    # Read the query string with key subject
    subject = request.args.get('subject')
    # Read the query string with key session
    session = request.args.get('session')

    # If either subject or session was not specified, return an error message
    if subject is None or session is None:
        return jsonify({'endpoint': request.path,
                        'error': 'NO SUBJECT OR SESSION SPECIFIED'})

    # Get list of all files and folders in the path
    lsout = (WORKINGDIR / 'EXPDATA' / subject / session).glob('*')

    # Get list of all files
    files = [str(i.parts[-1]) for i in lsout if i.is_file()]

    # Remove files that do not start with 'rec_'
    # files = [i for i in files if i[:4] == 'rec_']

    return jsonify({'endpoint': request.path, 'response': files})


@app.route('/data/record', methods=['GET'])
def data_record():
    """
    Get data from a given record.
    :return:
    """
    # Get the query string with key 'subject'
    subject = request.args.get('subject')
    # Get the query string with key 'session'
    session = request.args.get('session')
    # Get the query string with key 'record'
    record = request.args.get('record')

    # If any of the above are None, return an error message
    if subject is None or session is None or record is None:
        return jsonify({'endpoint': request.path,
                        'error': 'NO SUBJECT, SESSION OR RECORD SPECIFIED'})

    # Get the path to the record file
    record_file = WORKINGDIR / 'EXPDATA' / subject / session / record

    # If the file does not exist, return an error message
    if not record_file.is_file():
        return jsonify({'endpoint': request.path,
                        'error': 'FILE NOT FOUND'})

    # Read the file as a csv
    df = pd.read_csv(record_file)

    # Convert the dataframe to a python list of lists
    data = df.values.tolist()

    # Get the column names
    columns = df.columns.tolist()

    # Create a response dictionary
    response = {'endpoint': request.path,
                'response': {
                    'data': data,
                    'columns': columns
                }}

    return jsonify(response)

if __name__ == '__main__':

    # Handle app configuration

    # First check if there is a config file already.
    if CONFIGPATH.is_file():
        # Load configuration from file.
        print("Loading cofiguration from {}...".format(CONFIGPATH))
        APPCONFIG = toml.load(CONFIGPATH)
    else:
        print("Config file not found. Creating new default config file at {}...".format(CONFIGPATH))
        # Load the default configuration
        APPCONFIG = utils.DEFAULT_CONFIG
        # Create the config file and folder if it does not exist.
        CONFIGPATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIGPATH, 'w') as fp:
            toml.dump(APPCONFIG, fp)

    app.debug = True
    app.run(host='0.0.0.0', port=5050)
