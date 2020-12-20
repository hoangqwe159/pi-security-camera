# import required modules
from __future__ import print_function
from flask import Flask, render_template, Response 
from datetime import datetime
from datetime import date
import numpy as np
import imutilsimport time
import cv2
import sys
from smtplib import SMTP
from smtplib import SMTPException
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import smtplib
import mimetypes
import email
import email.mime.application
from smtplib import SMTP
from smtplib import SMTPException



app = Flask(__name__) 
vc = cv2.VideoCapture(0)
motionDectected = False
notifSent = False

# initialize the video stream and allow the camera sensor to warmup
print("[INFO] warming up camera...")


time.sleep(2.0)

# initialize the video writer and the frame dimensions (we'll set
# them as soon as we read the first frame from the video)
writer = None
W = None
H = None
avg = None
sendTime = None

def send(source):
    # Create a text/plain message
    msg = MIMEMultipart()
    msg['Subject'] = 'Security Feed'
    msg['From'] = 'finalprojectibf102@gmail.com'
    msg['To'] = 'doviethoang159@gmail.com'

     
    # The main body is just another attachment

     
    # attachment block code
    directory = source
     
    # Split the directory into fields separated by / to substract filename
     
    spl_dir=directory.split('/')
    
    # We attach the name of the file to filename by taking the last
    # position of the fragmented string, which is, indeed, the name
    # of the file we've selected
     
    filename=spl_dir[len(spl_dir)-1]
     
    # We'll do the same but this time to extract the file format 
    spl_type=directory.split('.')
     
    type=spl_type[len(spl_type)-1]
     
    fp=open(directory,'rb')
    att = email.mime.application.MIMEApplication(fp.read(),_subtype=type)
    fp.close()
    att.add_header('Content-Disposition','attachment',filename=filename)
    msg.attach(att)
     
    # send via Gmail server
    # NOTE: my ISP, Centurylink, seems to be automatically rewriting
    # port 25 packets to be port 587 and it is trashing port 587 packets.
    # So, I use the default port 25, but I authenticate.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login('finalprojectibf102@gmail.com','G7x6h0_N1')
    s.sendmail('finalprojectibf102@gmail.com','doviethoang159@gmail.com', msg.as_string())
    s.quit()

@app.route('/') 
def index(): 
   """Video streaming .""" 
   return render_template('index.html') 



def gen(): 
 
    global writer, W, H, avg, motionDectected, sendTime
    while True: 
        rval, frame = vc.read() 

        preMotionDetected =motionDectected
        # quit if there was a problem grabbing a frame
        if frame is None:
            break

        # resize the frame and convert the frame to grayscale
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the average frame is None, initialize it
        if avg is None:
            print("[INFO] starting background model...")
            avg = gray.copy().astype("float")
            
            continue

        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        cv2.accumulateWeighted(gray, avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, 5, 255,
            cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # if the frame dimensions are empty, set them
        if W is None or H is None:
            (H, W) = frame.shape[:2]

        if len(cnts) > 0:
            #cnts is the list of objects which are in motion
            for c in cnts:
                # compute the bounding box for the contour, draw it on the frame,
                # and update the text
                if cv2.contourArea(c) > 5000:
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    motionDectected = True     
        else:
            motionDectected = False

        # if the motion is detected and previously it was not detected, it means
        # the something has been just happened
        if motionDectected and not preMotionDetected: 
            # record the start time
            startTime = datetime.now()
            writer = cv2.VideoWriter('output.mp4',0x21, 10.0, (W, H),
                True)
        #if there is currently no motion detected and previously the motion was detected,
        #it means the action has been ended
        elif preMotionDetected and not motionDectected:
            endTime = datetime.now()
            totalSeconds = (endTime - startTime).seconds
            dateOpened = date.today().strftime("%A, %B %d %Y")
            msg = "Motion was detected on {} at {} for {} " \
                "seconds.".format(dateOpened,
                startTime.strftime("%I:%M%p"), totalSeconds)
            writer.release()
            print(msg)
           
            if totalSeconds >= 7 and totalSeconds <= 1800:
                print('video saved')
                if sendTime == None:
                    send('output.mp4')
                    sendTime = datetime.now()
                    print('sent vid')
                elif (datetime.now() - sendTime).seconds > 600:
                    send('output.mp4')
                    sendTime = datetime.now()
                    print('sent')
                    
                    
                    
            writer = None


            
        if writer is not None:
            writer.write(frame)
            print('writting')

        cv2.imwrite('pic.jpg', frame)
        
        
        yield (b'--frame\r\n' 
                b'Content-Type: image/jpeg\r\n\r\n' + open('pic.jpg', 'rb').read() + b'\r\n')
         
         
       
       
@app.route('/video_feed') 
def video_feed(): 
   """Video streaming route. Put this in the src attribute of an img tag.""" 
   return Response(gen(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame') 
if __name__ == '__main__': 
    app.run(host='0.0.0.0', threaded=True) 

