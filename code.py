from twilio.rest import Client
import time
import serial
import pynmea2
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
port = "/dev/ttyAMA0"  # serial port

# create a serial object
ser = serial.Serial(port, baudrate=9600, timeout=0.5)
try:
    while True:
        button_state = GPIO.input(23)
        account_sid = ""
        auth_token = ""
        # button pressed
        if button_state == False:
            # send first text message
            msg = "Help, I'm in danger"
            client = Client(account_sid, auth_token)
            client.api.account.messages.create(
                to="", from_="", body=msg)

            # start a 5 second timer to stop.
            t_end = time.time()+5
            while time.time() < t_end:
                button_state = True
                button_state = GPIO.input(23)

                # button pressed again
                if button_state == False:
                    # send false alarm message
                    msg = "Nevermind. False alarm."
                    client = Client(account_sid, auth_token)
                    client.api.account.messages.create(
                        to="", from_="", body=msg)
                    quit()

            # did not press button again | did not enter false alarm loop

            # camera starts recording for 10 seconds and saves
            camera = PiCamera()
            camera.start_preview()
            camera.start_recording('/home/pi/Desktop/video1.h264')
            sleep(10)
            camera.stop_recording()
            camera.stop_preview()
            camera.close()

            # get gps coordinates using gps module
            try:
                while 1:
                    try:
                        data = ser.readline()
                    except:
                        print("loading")

                    # wait for the serial port to churn out data
                    # the long and lat data are in the GPGGA string of the NMEA data
                    if data[0:6] == '$GPGGA':
                        msg = pynmea2.parse(data)

                        # parse latitude
                        latval = msg.lat
                        dd = int(float(latval)/100)
                        mm = float(latval)-dd*100
                        latDec = dd+mm/60

                        # parse longitude
                        longval = msg.lon
                        d2 = int(float(longval)/100)
                        m2 = float(longval)-d2*100
                        longDec = d2+m2/60

                        # send second text message with coordinates and map link
                        msg = "Lat:" + str(latDec)+"\t"+"Long:"+str(longDec)+" n" + \
                            "http://www.google.com/maps?q=" + \
                            str(latDec)+","+str(longDec)+",15z"
                        client = Client(account_sid, auth_token)
                        client.api.account.messages.create(
                            to="", from_="", body=msg)
                        time.sleep(2)
                        break
            except KeyboardInterrupt:
                GPIO.cleanup()
except:
    GPIO.cleanup()