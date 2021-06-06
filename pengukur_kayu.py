#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# import package
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import RPi.GPIO as GPIO
import time

def midpoint(ptA, ptB):
	return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)

# intialize the camera recording
camera = cv2.VideoCapture(0)
Detectou = False #just an aux variable
servoPIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)
GPIO.setwarnings(False)
p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
p.start(2.5) # Initialization
while(1):

	# loading gambar, mengubahnya menjadi skala abu-abu, dan membuat blur sedikit
	ret, image = camera.read()
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (7, 7), 0)

	# perform edge detection, then perform a dilation + erosion to
	# close gaps in between object edges
	edged = cv2.Canny(gray, 50, 100)
	edged = cv2.dilate(edged, None, iterations=1)
	edged = cv2.erode(edged, None, iterations=1)

	# find contours in the edge map
	cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = cnts[0] if imutils.is_cv2() else cnts[0]

	# sort the contours from left-to-right and initialize the
	# if no object were recognized after a recognition the program will stop with error
	try:
		(cnts, _) = contours.sort_contours(cnts)
		Detectou = True
	except: 
		#if Detectou: raise Parou_De_Detectar
		#else: pass
		pass
	# 'pixels per metric' calibration variable
	pixelsPerMetric = None
	img = image.copy()
	# loop over the contours individually
	for c in cnts:
		# if the contour is not sufficiently large, ignore it
		if cv2.contourArea(c) < 250:
			continue

		# compute the rotated bounding box of the contour
		#img = image.copy()
		box = cv2.minAreaRect(c)
		box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
		box = np.array(box, dtype="int")

		# order the points in the contour such that they appear
		# in top-left, top-right, bottom-right, and bottom-left
		# order, then draw the outline of the rotated bounding
		# box
		box = perspective.order_points(box)
		cv2.drawContours(img, [box.astype("int")], -1, (0, 255, 0), 2)

		# loop over the original points and draw them
		for (x, y) in box:
			cv2.circle(img, (int(x), int(y)), 5, (0, 0, 255), -1)

		# unpack the ordered bounding box, then compute the midpoint
		# between the top-left and top-right coordinates, followed by
		# the midpoint between bottom-left and bottom-right coordinates
		(tl, tr, br, bl) = box
		(tltrX, tltrY) = midpoint(tl, tr)
		(blbrX, blbrY) = midpoint(bl, br)

		# compute the midpoint between the top-left and top-right points,
		# followed by the midpoint between the top-righ and bottom-right
		(tlblX, tlblY) = midpoint(tl, bl)
		(trbrX, trbrY) = midpoint(tr, br)

		# draw the midpoints on the image
		cv2.circle(img, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
		cv2.circle(img, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
		cv2.circle(img, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
		cv2.circle(img, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)

		# draw lines between the midpoints
		cv2.line(img, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
			(255, 0, 255), 2)
		cv2.line(img, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
			(255, 0, 255), 2)

		# compute the Euclidean distance between the midpoints
		dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
		dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

		# if the pixels per metric has not been initialized, then
		# compute it as the ratio of pixels to supplied metric
		# (in this case, inches)
		if pixelsPerMetric is None:
			pixelsPerMetric = dB /5.0

		# compute the size of the object
		dimA = dA / pixelsPerMetric
		dimB = dB / pixelsPerMetric
		
		print("Dimensi A :", dimA)
		print("Dimensi B: ",dimB)

		if dimA >= 20.0:
			p.ChangeDutyCycle(7.5)
			print("Panjang kayu" , dimA)
			# time.sleep(1.0)
		else:
			p.ChangeDutyCycle(2.5)

		# draw the object sizes on the image
		cv2.putText(img, "{:.1f}cm".format(dimA),
			(int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
			0.65, (255, 255, 255), 2)
		cv2.putText(img, "{:.1f}cm".format(dimB),
			(int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
			0.65, (255, 255, 255), 2)
		
     

		# show the output image
	cv2.imshow("Pengukur Panjang Kayu", img)

	if cv2.waitKey(1) & 0xFF == ord('q'):
    	 break
# Release handle to the webcam
camera.release()
cv2.destroyAllWindows()
