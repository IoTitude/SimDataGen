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
	threads = None
	delay_time = 1
	locationList = []
	ax1 = None
	defaultid = 100
	defaultname = 11
	
	# Initialize database object
	cas_conn = DatabaseSession()

	#Constructor
	def __init__(self, delay_time=5):

		self.time = get_time_format()
		self.delay_time = delay_time
		self.locationList = []
		self.ax1 = None
		self.defaultid = 100
		self.defaultname = 11

	#Methods

	def calculations(self, i, t, former_f, last):
		# calculations for all locations in locationlist
		self.locationList[i].tyonto()

		f_next = self.locationList[i].get_pressure()

		self.locationList[i].countWaterLevel(t, self.locationList[i].pressure, former_f, last)

		log_data("SDG_bl/calculations", "made calculations to location: " + self.locationList[i].name + ", time: " + str(t), False)

		return f_next

	# Threading function
	def meterwell_thread(self, arg):
		id_same = False
		i = 0
		former_f = 0.0

		# Get all id's from the database so we can compare them to the current id
		db_ids = self.cas_conn.fetch_ids()

		t = 1.0

		self.threading_is = True

		while (self.threading_is == True):

			# Suspend execution for 5 seconds
			sleep(self.delay_time)

			i = 0

			if (t != 36):
				t = t + 0.01
			else:
				t = 1.0

			while (i < len(self.locationList)):

				current_id = self.locationList[i].get_wellid()

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

				self.time = get_time_format()

				self.cas_conn.send_meterwell_data(id_same, current_id, self.locationList[i].name, self.locationList[i].eastloc, self.locationList[i].northloc, self.locationList[i].well_level, self.locationList[i].temperature, self.locationList[i].conductivity, self.locationList[i].pressure, self.locationList[i].watersurface, self.locationList[i].flowrate)

				log_data("SDG_bl/thread_script", "Inserted location " + self.locationList[i].name + " to the database. Vedenpinta: " + str(self.locationList[i].watersurface), False)

				former_f = self.locationList[i].get_pressure()

				log_data("SDG_bl/thread_script", "Former pressure: " + str(former_f) + ", Current pressure: " + str(self.locationList[i].get_pressure()), False)

				i = i + 1


	# Threading frame
	def thread_init(self):
		try:
			# Set the target function and arguments for thread
			self.threads = Thread(target = self.meterwell_thread, args = (1, ))

			self.threads.start()

			log_data("SDG_bl/run_indef", "Started thread", False)

		except Exception as e:
			print e
			sys.exit()

	# Close running thread and database connection
	def database_close(self):
		if (self.threading_is == True):
			# Set threading_is variable to false so the thread will close
			self.threading_is = False

			# Wait for active threads to finish
			self.threads.join()
		# Close database connection
		self.cas_conn.close_connection()

		log_data("SDG_bl/database_close", "Closed database", False)

	def set_delay_time(self, delay_time):
		
		self.delay_time = int(delay_time)

		log_data("SDG_bl/set_delay_time", "Altered delay time", False)

	def check_database_connection(self):
		connection = self.cas_conn.get_connection()
		
		return connection

	def check_location(self, selected_loc):
		i = 0
		check_result = False
		while (i <= len(self.locationList)):
			if (int(selected_loc) == i):
				check_result = True
			i = i + 1
				
		return check_result

	def show_locations(self):
		i = 0
		while (i < len(self.locationList)):
			print str(i) + ". " + str(self.locationList[i].get_name()) + "\n"
			i = i + 1

	def check_parameters(self, selected_parameter):
		i = 0
		check_result = False
		while (i <= 5):
			if (int(selected_parameter) == i):
				check_result = True
			i = i + 1

		return check_result

	def show_parameters(self):
		print "0. Name\n1. East location\n2. North location\n3. Well level\n4. Incoming well\n5. Outgoing well"

	# Chnge the name of a well location
	def change_name(self, selected_loc):
		pattern = "loc-[0-9]{1,}"
		answer = raw_input("Enter new name (format: loc-[number]): ")
		if (re.search(pattern, answer)):
			self.locationList[int(selected_loc)].set_name(answer)
		else:
			print "Enter a valid name!"

	def check_name_input(self, user_input):
		pattern = "loc-[0-9]{1,}"
		if (re.search(pattern, user_input)):
			return True
		else:
			return False

	def display_locations(self):
		locations = self.cas_conn.location_data()
		rowcount = self.cas_conn.fetch_rowcount()
		nameList = [None] * rowcount[0]
		waterList = [None] * rowcount[0]
		flowList = [None] * rowcount[0]

		for eachLine in locations:
		
			i = 0
			while (i <= rowcount[0]):
				if (eachLine[0] == "loc-" + str(i + 1)):
					nameList[i] = eachLine[0]
					waterList[i] = eachLine[1]
					flowList[i] = eachLine[2]

				i = i + 1

		log_data("SDG_bl/animate", "nameList: " + str(nameList) + "\n" + str(waterList) + "\n" + str(flowList), False)

		i = 0
		while (i < rowcount[0]):
			print "Name: " + str(nameList[i]) + "			Water surface: " + str(waterList[i]) + "			Water flow: " + str(flowList[i])
			i = i + 1


	def display_well(self, well):
		location_data = self.cas_conn.fetch_well_data()
		rowcount = self.cas_conn.fetch_rowcount()
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

		print "ID     " + "Name     " + "Vedenpinta     " + "Virtausnopeus        " + "East     " + "North     " + "Water level     " + "Pressure     " + "Conductivity     " + "Temperature     \n"
		print str(well_data[0]) + "     " + str(well_data[1]) + "     " + str(well_data[2]) + "       " + str(well_data[3]) + "     " + str(well_data[4]) + "        " + str(well_data[5]) + "         " + str(well_data[6]) + "             " + str(well_data[7]) + "         " + str(well_data[8]) + "              " + str(well_data[9]) + "\n"

	# Change the location information of an incoming well
	def change_incoming_well(self, selected_loc):
		answer = raw_input("Enter new incoming well level: ")
		self.locationList[int(selected_loc)].set_inc_flow_well(int(answer))

		answerE = raw_input("Enter new incoming well east location: ")
		answerN = raw_input("Enter new incoming well north location: ")
		self.locationList[int(selected_loc)].set_inc_pipe_loc(int(answerE), int(answerN))

	# Change the lcation information of an outgoing well
	def change_outgoing_well(self, selected_loc):
		answer = raw_input("Enter new incoming well level: ")
		self.locationList[int(selected_loc)].set_out_flow_well(int(answer))

		answerE = raw_input("Enter new incoming well east location: ")
		answerN = raw_input("Enter new incoming well north location: ")
		self.locationList[int(selected_loc)].set_out_pipe_loc(int(answerE), int(answerN))

	# Change well parameters
	def change_parameter(self, selected_loc, selected_parameter):
		if (selected_parameter == "0"):
			self.change_name(selected_loc)

		elif (selected_parameter == "1"):
			answer = raw_input("Enter new east location: ")
			self.locationList[int(selected_loc)].set_eastloc(int(answer))

		elif (selected_parameter == "2"):
			answer = raw_input("Enter new north location: ")
			self.locationList[int(selected_loc)].set_northloc(int(answer))

		elif (selected_parameter == "3"):
			answer = raw_input("Enter new well level: ")
			self.locationList[int(selected_loc)].set_well_level(int(answer))

		elif (selected_parameter == "4"):
			self.change_incoming_well(selected_loc)

		elif (selected_parameter == "5"):
			self.change_outgoing_well(selected_loc)

	# Function called from SDG_main
	def start_test(self):

		# Connect to database
		self.cas_conn.establish_connection()

		self.locationList.append(MeterWell(0, "test", 1, 1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1))

		log_data("SDG_bl/start_test", "Simulation test started", True)

		self.thread_init()

		con_success = self.cas_conn.get_connection()

	def animate(self, i):
		pullData = self.cas_conn.fetch_watersurface()
		pullName = self.cas_conn.fetch_name()
		rowcount = self.cas_conn.fetch_rowcount()
		nameList = [None] * rowcount[0]
		errList = [None] * rowcount[0]
		resultList = [None] * rowcount[0]
		correctresList = [None] * rowcount[0]
		xar = []
		yar = []

		xar.append(0)
		yar.append(0)

		log_data("SDG_bl/animate", "resultList: " + str(resultList) + ", nameList: " + str(nameList), False)

		# Sort nameList in the correct order and fill errList with the incorrect order existing in the database
		t = 0
		for eachName in pullName:

			errList[t] = str(eachName[0])

			u = 0
			while (u <= rowcount[0]):
				locName = "loc-" + str(u)

				if (eachName[0] == locName):
					nameList[u - 1] = str(eachName[0])
				u = u + 1

			log_data("SDG_bl/animate", "NameList in progress: " + str(nameList), False)
			t = t + 1

		log_data("SDG_bl/animate", "NameList: " + str(nameList) + " Error list: " + str(errList), False)

		# Compare nameList and errList to sort resultList in the correct order
		t = 0
		for eachLine in pullData:

			u = 0
			while (u < rowcount[0]):
				
				if (errList[t] == nameList[u]):

					correctresList[u] = eachLine[0]
				
				u = u + 1

			log_data("SDG_bl/animate", "Resultlist in progress: " + str(correctresList), False)
			t = t + 1

		log_data("SDG_bl/animate", "correctresList: " + str(correctresList) + ", nameList: " + str(nameList), False)

		# Set the correctly ordered lists together
		o = 0
		i = 1
		while (o < rowcount[0]):

			xar.append(i)
			yar.append(correctresList[o])
			log_data("SDG_bl/animate", "Location name: " + str(nameList[o]) + ", Result: " + str(correctresList[o]), False)
			i = i + 1
			o = o + 1

		self.ax1.clear()
		self.ax1.plot(xar, yar)


	# Function for fetching data from the database and displaying it at set intervals
	def run_animation(self):

		# start matplotlib figure
		fig = plt.figure()
		self.ax1 = fig.add_subplot(1,1,1)
		ani = animation.FuncAnimation(fig, self.animate, interval=1000) # update every second
		plt.show()

	def clear_wells(self):
		delids = 100
		db_ids = self.cas_conn.fetch_ids()
		idList = []
		rowcount = self.cas_conn.fetch_rowcount()

		for user_id in db_ids:
			idList.append(str(user_id[0]))

		log_data("SDG_bl/clear_wells", "IDlist: " + str(idList), False)

		i = 0
		while (i <= rowcount[0] - 1):
			removeId = idList[i]
			log_data("SDG_bl/clear_wells", "DB_ID: " + str(removeId), False)
			if (removeId >= delids):
				self.cas_conn.delete_row(removeId)
				delids = delids + 1
			i = i + 1

	def add_new_well(self, east, north, well_level, inc_flow, out_flow, XE, XN, YE, YN, welltype):

		name = "loc-" + str(self.defaultname)

		self.locationList.append(MeterWell(self.defaultid, name, east, north, well_level, inc_flow, out_flow, XE, XN, YE, YN, welltype))
		self.defaultid = self.defaultid + 1
		self.defaultname = self.defaultname + 1

	# Function for starting the simulation for 10 different measurement wells
	def start_simulation(self):

		# Connect to database
		self.cas_conn.establish_connection()

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
			self.locationList[i].set_pipe_diameters()
			i = i + 1

		log_data("SDG_bl/start_simulation", "Added 10 locations", True)

		self.thread_init()