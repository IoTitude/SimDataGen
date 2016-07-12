# SimDataGen Business logic layer

from database_connect import DatabaseSession
from measurement_location import MeterWell
import sys
from threading import Thread
from time import sleep
import time
from data_format import *
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re

class SimDataGen(object):

	#Attributes
	time = None
	threading_is = False
	threading_is2 = False
	threads = None
	threads2 = None
	delay_time = 1
	locationList = []
	ax1 = None
	defaultid = 100
	defaultname = 11
	errorwellList = []
	errornumList = []
	
	# Initialize database object
	cas_conn = DatabaseSession()
	cas_conn2 = DatabaseSession()

	#Constructor
	def __init__(self, delay_time=5):

		self.time = getTimeFormat()
		self.delay_time = delay_time
		self.locationList = []
		self.ax1 = None
		self.defaultid = 100
		self.defaultname = 11

		self.errorwellList = []
		self.errornumList = []

	#Methods

	def calculations(self, i, t, former_f, last):
		# Calculations for all locations in locationlist
		self.locationList[i].tyonto()

		f_next = self.locationList[i].getPressure()

		self.locationList[i].countWaterLevel(t, self.locationList[i].pressure, former_f, last)

		return f_next

	# Threading function
	def meterwellThread(self, arg):
		try:
			id_same = False
			i = 0
			former_f = 0.0

			# Get all id's from the database so we can compare them to the current id
			db_ids = self.cas_conn.fetchIds()

			t = 1.0

			self.threading_is = True

			while (self.threading_is == True):

				# Suspend execution for the amount of time specified in delay_time
				sleep(self.delay_time)

				i = 0

				if (t != 36):
					t = t + 0.01
				else:
					t = 1.0

				while (i < len(self.locationList)):

					current_id = self.locationList[i].getWellid()

					if (i + 1 == len(self.locationList)):
						receive_f = self.calculations(i, t, former_f, True)
					else:
						receive_f = self.calculations(i, t, former_f, False)

					# Check if our current id already exists in the database
					for user_id in db_ids:
						if (current_id == user_id):
							id_same = True
						else:
							id_same = False

					self.time = getTimeFormat()

					self.cas_conn.sendMeterwellData(id_same, current_id, self.locationList[i].name, self.locationList[i].eastloc, \
					self.locationList[i].northloc, self.locationList[i].well_level, self.locationList[i].temperature, self.locationList[i].conductivity, \
					self.locationList[i].pressure, self.locationList[i].watersurface, self.locationList[i].flowrate)

					former_f = self.locationList[i].getPressure()

					i = i + 1

		except Exception as e:
			logData("SDG_bl/meterwellThread", str(e), False)
			print e

	def thousandMeterThread(self, wellamount):

		try:
			db_ids = self.cas_conn2.fetchIds()

			id_same = False
			increment = 10
			incrementparam = 0

			self.threading_is2 = True

			while (self.threading_is2 == True):

				i = 0
				wellid = 1000

				if (incrementparam > 60):
					incrementparam = 0
			
				# Suspend execution for the amount of time specified in delay_time
				sleep(self.delay_time)

				while (i <= wellamount):
					# Check if our current id already exists in the database
					for user_id in db_ids:
						if (wellid == user_id):
							id_same = True
						else:
							id_same = False

					self.cas_conn2.sendMeterwellData(id_same, wellid, "loc-" + str(wellid), wellid, wellid, wellid, wellid, wellid, 0, incrementparam, incrementparam)

					wellid = wellid + 1
					i = i + 1

				incrementparam = incrementparam + increment

		except Exception as e:
			logData("SDG_bl/thousandMeterThread", str(e), False)



	# Threading frame
	def threadInit(self, choice, wellamount):
		try:
			if (choice == 1):
				# Set the target function and arguments for thread
				self.threads = Thread(target = self.meterwellThread, args = (1, ))

				self.threads.start()

			elif (choice == 2):
				# Set the target function and arguments for thread
				self.threads2 = Thread(target = self.thousandMeterThread, args = (wellamount, ))

				self.threads2.start()

		except Exception as e:
			print e
			sys.exit()

	# Close running thread and database connection
	def databaseClose(self):
		try:
			skip1 = False
			skip2 = False

			if (self.threading_is == True):
				# Set threading_is variable to false so the thread will close
				self.threading_is = False
			else:
				skip1 = True

			if (self.threading_is2 == True):
				# Set threading_is variable to false so the thread will close
				self.threading_is2 = False
			else:
				skip2 = True

			# Wait for active threads to finish
			if (skip1 == False):
				self.threads.join()
			if (skip2 == False):
				self.threads2.join()

			# Close database connection
			if (skip1 == False):
				self.cas_conn.closeConnection()
			if (skip2 == False):
				self.cas_conn2.closeConnection()

		except Exception as e:
			logData("SDG_bl/databaseClose", str(e), False)

	def setDelayTime(self, delay_time):
		
		self.delay_time = int(delay_time)

	def checkDatabaseConnection(self):
		connection1 = self.cas_conn.getConnection()

		connection2 = self.cas_conn2.getConnection()
		
		if (connection1 == True):
			return connection1
		if (connection2 == True):
			return connection2
		else:
			return False

	def checkLocation(self, selected_loc):
		i = 0
		check_result = False
		while (i <= len(self.locationList)):
			if (int(selected_loc) == i):
				check_result = True
			i = i + 1
				
		return check_result

	def showLocations(self):
		i = 0
		while (i < len(self.locationList)):
			print str(i) + ". " + str(self.locationList[i].getName()) + "\n"
			i = i + 1

	def checkParameters(self, selected_parameter):
		i = 0
		check_result = False
		while (i <= 5):
			if (int(selected_parameter) == i):
				check_result = True
			i = i + 1

		return check_result

	def showParameters(self):
		print "0. East location\n1. North location\n2. Well level\n3. Incoming well\n4. Outgoing well"

	def checkNameInput(self, user_input):
		pattern = "loc-[0-9]{1,}"
		if (re.search(pattern, user_input)):
			return True
		else:
			return False

	def validateNumber(self, delay_time):
		pattern = "^\d*$"
		if (re.search(pattern, delay_time)):
			return True
		else:
			return False

	def displayLocations(self):
		locations = self.cas_conn.locationData()
		rowcount = self.cas_conn.fetchRowcount()
		nameList = [None] * 10
		waterList = [None] * 10
		flowList = [None] * 10

		for eachLine in locations:
		
			i = 0
			while (i < 10):
				if (eachLine[0] == "loc-" + str(i + 1)):
					nameList[i] = eachLine[0]
					waterList[i] = eachLine[1]
					flowList[i] = eachLine[2]

				i = i + 1

		i = 0
		while (i < 10):
			print str(i) + ". " + str(nameList[i]) + "			Water surface: " + str(waterList[i]) + "			Water flow: " + str(flowList[i]) + "\n"
			i = i + 1


	def displayWell(self, well):
		location_data = self.cas_conn.fetchWellData()
		rowcount = self.cas_conn.fetchRowcount()
		well_data = [None] * rowcount[0]

		for eachLine in location_data:

			if (well == eachLine[1]):
				well_data[0] = eachLine[0]
				well_data[1] = eachLine[1]
				well_data[2] = eachLine[2]
				well_data[3] = eachLine[3]
				well_data[4] = eachLine[4]
				well_data[5] = eachLine[5]
				well_data[6] = eachLine[6]
				well_data[7] = eachLine[7]
				well_data[8] = eachLine[8]
				well_data[9] = eachLine[9]

		print "ID     " + "Name     " + "Vedenpinta     " + "Virtausnopeus        " + \
		"East     " + "North     " + "Water level     " + "Pressure     " + "Conductivity     " + \
		"Temperature     \n"

		print str(well_data[0]) + "     " + str(well_data[1]) + "     " + str(well_data[2]) + \
		"       " + str(well_data[3]) + "     " + str(well_data[4]) + "        " + str(well_data[5]) + \
		"         " + str(well_data[6]) + "             " + str(well_data[7]) + "         " + str(well_data[8]) + \
		"              " + str(well_data[9]) + "\n"

	# Change the location information of an incoming well
	def changeIncomingWell(self, selected_loc):
		answer = raw_input("Enter new incoming well level: ")
		self.locationList[int(selected_loc)].setIncFlowWell(int(answer))

		answerE = raw_input("Enter new incoming well east location: ")
		answerN = raw_input("Enter new incoming well north location: ")
		self.locationList[int(selected_loc)].setIncPipeLoc(int(answerE), int(answerN))

	# Change the lcation information of an outgoing well
	def changeOutgoingWell(self, selected_loc):
		answer = raw_input("Enter new incoming well level: ")
		self.locationList[int(selected_loc)].setOutFlowWell(int(answer))

		answerE = raw_input("Enter new outgoing well east location: ")
		answerN = raw_input("Enter new outgoing well north location: ")
		self.locationList[int(selected_loc)].setOutPipeLoc(int(answerE), int(answerN))

	# Change well parameters
	def changeParameter(self, selected_loc, selected_parameter):
		
		if (selected_parameter == "0"):
			answer = raw_input("Enter new east location: ")
			self.locationList[int(selected_loc)].setEastloc(int(answer))

		elif (selected_parameter == "1"):
			answer = raw_input("Enter new north location: ")
			self.locationList[int(selected_loc)].setNorthloc(int(answer))

		elif (selected_parameter == "2"):
			answer = raw_input("Enter new well level: ")
			self.locationList[int(selected_loc)].setWellLevel(int(answer))

		elif (selected_parameter == "3"):
			self.changeIncomingWell(selected_loc)

		elif (selected_parameter == "4"):
			self.changeOutgoingWell(selected_loc)

	def enableError(self, errorwell, error):
		
		self.locationList[int(errorwell)].setErrorMode(int(error))

		self.errorwellList.append(self.locationList[int(errorwell)].getName())
		self.errornumList.append(error)

	def disableErrors(self):
		i = 0
		while (i <= len(self.errorwellList)):
			self.locationList[i].setErrorMode(0)
			i = i + 1

	def animate(self, i):
		try:
			pullInfo = self.cas_conn.fetchInfo()
			nameList = [None] * 10
			resultList = [None] * 10
			xar = []
			yar = []

			xar.append(0)
			yar.append(0)

			# Sort nameList in the correct order and fill errList with the incorrect order existing in the database
			for eachInfo in pullInfo:

				if (eachInfo[0] == 1):
					nameList[0] = str(eachInfo[1])
					resultList[0] = str(eachInfo[2])

				elif (eachInfo[0] == 10):
					nameList[1] = str(eachInfo[1])
					resultList[1] = str(eachInfo[2])

				elif (eachInfo[0] == 20):
					nameList[2] = str(eachInfo[1])
					resultList[2] = str(eachInfo[2])

				elif (eachInfo[0] == 30):
					nameList[3] = str(eachInfo[1])
					resultList[3] = str(eachInfo[2])

				elif (eachInfo[0] == 40):
					nameList[4] = str(eachInfo[1])
					resultList[4] = str(eachInfo[2])

				elif (eachInfo[0] == 50):
					nameList[5] = str(eachInfo[1])
					resultList[5] = str(eachInfo[2])

				elif (eachInfo[0] == 60):
					nameList[6] = str(eachInfo[1])
					resultList[6] = str(eachInfo[2])

				elif (eachInfo[0] == 70):
					nameList[7] = str(eachInfo[1])
					resultList[7] = str(eachInfo[2])

				elif (eachInfo[0] == 80):
					nameList[8] = str(eachInfo[1])
					resultList[8] = str(eachInfo[2])

				elif (eachInfo[0] == 90):
					nameList[9] = str(eachInfo[1])
					resultList[9] = str(eachInfo[2])

			# Set the correctly ordered lists together
			a = 0
			i = 1
			while (a < len(resultList)):

				xar.append(i)
				yar.append(resultList[a])
				i = i + 1
				a = a + 1

			self.ax1.clear()
			self.ax1.plot(xar, yar)

		except Exception as e:
			logData("SDG_bl/animate", str(e), False)
			print e


	# Function for fetching data from the database and displaying it at set intervals
	def runAnimation(self):

		# start matplotlib figure
		fig = plt.figure()
		self.ax1 = fig.add_subplot(1,1,1)
		ani = animation.FuncAnimation(fig, self.animate, interval=1000) # update every second
		plt.show()

	def clearWells(self):
		delids = 100
		db_ids = self.cas_conn.fetchIds()
		idList = []
		rowcount = self.cas_conn.fetchRowcount()

		for user_id in db_ids:
			idList.append(str(user_id[0]))

		i = 0
		while (i <= rowcount[0] - 1):
			removeId = idList[i]
			if (removeId >= delids):
				self.cas_conn.deleteRow(removeId)
				delids = delids + 1
			i = i + 1

	def deletePrevious(self):
		rowcount = self.cas_conn2.fetchRowcount()
		wellid = 1000

		self.cas_conn2.deleteManyRows(wellid, rowcount)

	def addNewWell(self, east, north, well_level, inc_flow, out_flow, XE, XN, YE, YN, welltype):

		name = "loc-" + str(self.defaultname)

		self.locationList.append(MeterWell(self.defaultid, name, east, north, well_level, inc_flow, out_flow, XE, XN, YE, YN, welltype))
		self.defaultid = self.defaultid + 1
		self.defaultname = self.defaultname + 1

	def startThousandSimulation(self, wellamount):
		self.cas_conn2.establishConnection()

		logData("SDG_bl/startThousandSimulation", "Program started", True)

		self.deletePrevious()

		self.threadInit(2, wellamount)

	# Function for starting the simulation for 10 different measurement wells
	def startSimulation(self):

		# Connect to database
		self.cas_conn.establishConnection()

		# Create 10 wells with required data (id, name, east, north, well level, incoming flow to the well, outgoing flow to the well, incoming east location,
		# incoming north location, outgoing east location, outgoing north location, well type)
		self.locationList.append(MeterWell(1, "loc-1", 0, 5, 1, 0, 5, 0, 0, 4, 3, 4))
		self.locationList.append(MeterWell(10, "loc-2", 4, 3, 5, 1, 4, 0, 5, 7, 3, 3))
		self.locationList.append(MeterWell(20, "loc-3", 7, 3, 4, 5, 3, 4, 3, 12, 6, 1))
		self.locationList.append(MeterWell(30, "loc-4", 12, 6, 3, 4, 2, 7, 3, 19, 9, 1))
		self.locationList.append(MeterWell(40, "loc-5", 19, 9, 2, 3, 1, 12, 6, 22, 10, 1))
		self.locationList.append(MeterWell(50, "loc-6", 22, 10, 1, 2, 2, 19, 9, 23, 5, 2))
		self.locationList.append(MeterWell(60, "loc-7", 23, 5, 2, 1, 4, 22, 10, 34, 0, 4))
		self.locationList.append(MeterWell(70, "loc-8", 34, 0, 4, 2, 3, 23, 5, 36, 0, 3))
		self.locationList.append(MeterWell(80, "loc-9", 36, 0, 3, 4, 5, 34, 0, 51, 7, 2))
		self.locationList.append(MeterWell(90, "loc-10", 51, 7, 6, 3, 0, 36, 0, 0, 0, 3))

		i = 0
		while (i < len(self.locationList)):
			self.locationList[i].setPipeDiameters()
			i = i + 1

		logData("SDG_bl/startSimulation", "Program started", True)

		self.threadInit(1, 10)