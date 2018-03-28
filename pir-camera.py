import RPi.GPIO as GPIO
import time
import picamera
import requests
import json

GPIO.setmode(GPIO.BCM)

GPIO.setup(23, GPIO.IN) #PIR
GPIO.setup(2, GPIO.OUT)
GPIO.setup(3, GPIO.OUT)

n=0
motion_threshold = 0
motion_detected = False
camera = picamera.PiCamera()
url = 'https://gateway-a.watsonplatform.net/visual-recognition/api/v3/classify?api_key=959331b8d0af7b3c1e21d58543af5e22f17b3ace&version=2016-05-20'
#camera.capture('image.jpg')
#camera.start_preview()
#file = open('image.jpg', 'wb')

def image_analysis():
    # send photo to visual recognition
    files = {'image.jpg': open('/home/pi/image.jpg', 'rb')}
    response = requests.post(url, files=files)
    #print(response.json())
    #find face in jason
    human_classes = ["thumb", "skin", "person"]
    data = response.json()
    classes = data['images'][0]['classifiers'][0]['classes']
    for c in classes:
        if c['class'] in human_classes:
            print("human detected...")
            return True
    print("No human activities...")
    return False


#try:
time.sleep(2)
while True:
    if GPIO.input(23):
        n=n+1
        print("%d Motion detected..." % n)
        motion_threshold = motion_threshold + 1
        print("threshold is %d" % motion_threshold)
        if motion_threshold > 3:
            motion_detected = True
            GPIO.output(2,1)
            time.sleep(1) 
            # take a photo
            camera.capture("/home/pi/image.jpg", use_video_port=True)
            image_analysis()
            if image_analysis():
                GPIO.output(3,1)
            else:
                GPIO.output(3,0)
            motion_threshold = 0
            time.sleep(2)
        else:
            pass
    else:
        motion_detected = False
        GPIO.output(2,0)
        motion_threshold = 0
    time.sleep(1)
#except Exception as inst:
 #   print inst
  #  GPIO.cleanup()
