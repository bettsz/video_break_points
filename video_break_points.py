#!/usr/bin/env python3
import tkinter
from tkinter import Tk
from tkinter.filedialog import askopenfilename,askdirectory
import cv2
import numpy as np
import os
from os import path,walk
from pydub import AudioSegment,silence
from progress.bar import IncrementalBar
import time
import math
from math import floor

class Video:
	def __init__(self, location):
		self.location = location
		self.cap = cv2.VideoCapture(location)
		self.length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 5
		self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
		self.silence = self.setSilence()
		self.blank = self.setBlank()
		self.breakPoints = self.setBreakPoints()
		
	def setSilence(self):
		print("Gathering silences")
		#Create audio object from video
		myaudio = AudioSegment.from_file(self.location)
		#Search object for silence
		sil = silence.detect_silence(myaudio, min_silence_len=200, silence_thresh=-16)
		#Convert to frames
		sil = [[round(start/1000*self.fps),round(stop/1000*self.fps)] for start,stop in sil]
		print("Finished silences")
		return sil
		
	def setBlank(self):
		count = 0
		start = 0
		blank = []
		bar = IncrementalBar('Gathering blanks', max = self.length)
		
		#Loop through video frames
		while self.cap.isOpened():
			bar.next()
			ret, frame = self.cap.read()
			
			#Check if frame is blank
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			if np.average(gray) < 40:
				#Keep if this is the start of a range of blank frames
				if start == 0:
					start = count
			#If a range has ended track the end frame
			elif start != 0:
				if ((count - 1) - start) > 2:
					blank.append([start, count - 1])
				start = 0
			
			count += 1
			#Check if end of video
			if count > self.length-1:
				self.cap.release()
				#If video ended with blank screen track that as end of range
				if start != 0:
					if ((count - 1) - start) > 2:
						blank.append([start, count - 1])
				break
		
		bar.finish()
		print("Finished blanks")
		return blank

	def setBreakPoints(self):
		#Get silence and blank ranges to compare
		silence = self.silence
		blank = self.blank
		breakPoint = []
		
		bar = IncrementalBar('Gathering break points', max = len(silence))
		#Loop through silence ranges
		for silStart, silStop in silence:
			bar.next()
			#Loop through blank ranges
			for blStart, blStop in blank:
				start = None
				stop = None
				#Find starting point within the two ranges
				if silStart <= blStart <= silStop:
					start = blStart
				elif blStart <= silStart <= blStop:
					start = silStart
				#Find stopping point within the two ranges
				if silStart <= blStop <= silStop:
					stop = blStop
				elif blStart <= silStop <= blStop:
					stop = silStop
				#Output as range
				if start != None and stop != None:
					breakPoint.append([start, stop])
		bar.finish()
		return breakPoint

def findBreakPoints(location):
	if path.exists(location):
		name, extension = os.path.splitext(location)
		if extension in [".mkv", ".mp4", ".avi"]:
			print("Creating break points")
			video = Video(location)
			f = open(str(name)+".txt", "w")
			f.write("Break Points: "+str(findMidPoints(video.breakPoints)))
			f.write("\nTime breaks:"+str(framesToTimes(findMidPoints(video.breakPoints), video.fps)))
			f.write("\nBlanks: "+str(findMidPoints(video.blank)))
			f.close()
			print(str(name)+".txt updated with break points")
		else:
			print("Invalid file type: "+str(location))
	else:
		print("Invalid path: "+str(location))

def findMidPoints(array):
	newPoints = []
	if len(array) > 0:
		for set in array:
			point = set[0] + round((set[1] - set[0])/2)
			newPoints.append(point)
	return newPoints

def framesToTimes(frameList, fps):
	times = []
	if len(frameList) > 0:
		for frame in frameList:
			timestamp = floor(frame/fps)
			time = ""
			if timestamp >= 3600:
				hours = floor(timestamp/3600)
				timestamp -= hours*3600
				time += str(hours)+":"
			if timestamp >= 60:
				minutes = floor(timestamp/60)
				timestamp -= minutes*60
				if minutes < 10:
					time += "0"+str(minutes)+":"
				else:
					time += str(minutes)+":"
			else:
				time += "00:"
			if timestamp < 10:
				time += "0"+str(timestamp)
			else:
				time += str(timestamp)
			times.append(time)
	return times

Tk().withdraw()
cancel = False

while not cancel:
	fpath = askopenfilename()
	#question = input("Import file[f] or directory[d]?")
	#if question == "f":
	#	fpath = askopenfilename()
	#elif question == "d":
	#	fpath = askdirectory()
	#else:
	#	quit()

	print(fpath)
	if not fpath:
		cancel = True
	else:
		#Open file
		if os.path.isfile(fpath):
			findBreakPoints(fpath)
		#Open directory (testing)
		if os.path.isdir(fpath):
			f = []
			for (dirpath, dirnames, filenames) in walk(fpath):
				print(dirpath)
				print(dirnames)
				print(filenames)
				f.extend(filenames)
			#for file in f:
				#findBreakPoints(file)
