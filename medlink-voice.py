# *****************************************************************************
# Copyright (c) 2017 IBM Corporation and other Contributors.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html 
#
# *****************************************************************************

import time
import sys
import uuid
import argparse
import json
import os
import watson_developer_cloud
from os.path import join, dirname
import pyaudio  
import wave 

USERNAME = os.environ.get('TTS_USERNAME','388fe107-fca8-4dd1-9a6d-f7cfe55d1c7e')
PASSWORD = os.environ.get('TTS_PASSWORD','5J8jaELqd1WJ')
AUDIO_FILE = '/home/pi/med_alert.wav'

pidfile=open("/home/pi/pid.pid","w+")
pid=os.getpid()
pidfile.write("%s\n" % pid)
pidfile.close()

def text_to_speech(text):
    tts = watson_developer_cloud.TextToSpeechV1(username=USERNAME,password=PASSWORD)
    #text = 'Hi! This is a reminder from your doctor. Please take your medicine now'
    with open(join(dirname(__file__), AUDIO_FILE),
        'wb') as audio_file:
        audio_file.write(
            tts.synthesize(text, accept='audio/wav',voice="en-US_AllisonVoice").content)

def playAudio():
    #define stream chunk
    chunk = 1024  
    #open a wav format music  
    f = wave.open(AUDIO_FILE,"rb")  
    #instantiate PyAudio  
    p = pyaudio.PyAudio()  
    #open stream  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                    channels = f.getnchannels(),  
                    rate = f.getframerate(),  
                    output = True)  
    #read data  
    data = f.readframes(chunk)
    #play stream  
    while data:  
        stream.write(data)  
        data = f.readframes(chunk)
    #stop stream  
    stream.stop_stream()  
    stream.close()  
    #close PyAudio  
    p.terminate() 

try:
	import ibmiotf.device
except ImportError:
	# This part is only required to run the sample from within the samples
	# directory when the module itself is not installed.
	#
	# If you have the module installed, just use "import ibmiotf.device"
	import os
	import inspect
	cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../../src")))
	if cmd_subfolder not in sys.path:
		sys.path.insert(0, cmd_subfolder)
	import ibmiotf.device

def commandProcessor(cmd):
    print("Medical alert received: %s" % cmd.data)
    if cmd.command == "Command":
        if 'notification' in cmd.data:
            msg = cmd.data['notification']
            if len(msg) > 0:
                success = deviceCli.publishEvent(args.event, "json", cmd.data, qos=0)                
                # convert text to speech and store locally
                text_to_speech(msg)
                # logic to add here for human detection at dining area using PIR or camera
                # once a target is detected, play medical alert messages
                playAudio()
            else:
                print("message contains nothing")
        else:
            print("no message received")
    else:
        print("message not correct type")

authMethod = None

# Initialize the properties we need
parser = argparse.ArgumentParser()

# Primary Options
parser.add_argument('-o', '--organization', required=False, default="nxtixw")
parser.add_argument('-T', '--devicetype', required=False, default="pi")
parser.add_argument('-I', '--deviceid', required=False, default="medlink")
parser.add_argument('-t', '--token', required=False, default='ASDFGHJKL', help='token')
parser.add_argument('-c', '--cfg', required=False, default=None, help='configuration file')
parser.add_argument('-E', '--event', required=False, default="event", help='type of event to send')
parser.add_argument('-N', '--nummsgs', required=False, type=int, default=999999, help='send this many messages before disconnecting') 
parser.add_argument('-D', '--delay', required=False, type=float, default=5, help='number of seconds between msgs') 
args, unknown = parser.parse_known_args()

if args.token:
	authMethod = "token"

# Initialize the device client.

try:
	if args.cfg is not None:
		deviceOptions = ibmiotf.device.ParseConfigFile(args.cfg)
	else:
		deviceOptions = {"org": args.organization, "type": args.devicetype, "id": args.deviceid, "auth-method": authMethod, "auth-token": args.token}
	deviceCli = ibmiotf.device.Client(deviceOptions)
	deviceCli.commandCallback = commandProcessor
except Exception as e:
	print("Caught exception connecting device: %s" % str(e))
	sys.exit()

# Connect and send datapoint(s) into the cloud
deviceCli.connect()
for x in range (0, args.nummsgs):
	data = { 'status' : 'ok'}
	def myOnPublishCallback():
		print("Confirmed event %s received by IoTF\n" % x)
	print("Publish status")
        success = deviceCli.publishEvent(args.event, "json", data, qos=0, on_publish=myOnPublishCallback)
	if not success:
		print("Not connected to IoTF")

	time.sleep(args.delay)

# Disconnect the device and application from the cloud
deviceCli.disconnect()
