from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from data_format import *

# get metadata regarding database from a separate file
import imp
modl = imp.load_source('data_file', 'src/data_file.py')


class DatabaseSession(object):

	#Attributes
	username = None
	password = None
	keyspace = None
	session = None
	connection = False
	node_ips = None
	port = None
	metadata = None

	#Constructor
	def __init__(self, uname="", pword="", kspace="", _node_ips="", _port=""):

		self.username = modl.getUsername()
		self.password = modl.getPassword()
		self.keyspace = modl.getKeyspace()
		self.session = None
		self.connection = False
		self.node_ips = modl.getNodeIps()
		self.port = modl.getPort()
		self.metadata = None


	#Methods
	# Connect to the database and set connection to true
	def establishConnection(self):
		if (self.connection == False):
			try:
				auth_provider = PlainTextAuthProvider(username = self.username, password = self.password)

				cluster = Cluster(self.node_ips, auth_provider = auth_provider, port = self.port)
				self.metadata = cluster.metadata

				self.session = cluster.connect(self.keyspace)
				print "Connected to cluster: " + self.metadata.cluster_name
				print self.session
				self.connection = True

			except Exception, e:
				logData("database_connect/establishConnection", str(e), False)
				print "Database Error: ", e
		else:
			print "Error: Connection already established!"

	def locationData(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				locdata = self.session.execute("SELECT nimi, vedenpinta, virtausnopeus FROM " + table)
				return locdata
			except Exception as e:
				logData("database_connect/locationData", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get location data from database"

	def fetchWellData(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				locdata = self.session.execute("SELECT id, nimi, vedenpinta, virtausnopeus, east, north, korkeus_merenpinnasta, paine, ominaissahkojohtavuus, lampotila FROM " + table)
				return locdata
			except Exception as e:
				logData("database_connect/fetchWellData", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get well data from database"

	def fetchInfo(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				db_info = self.session.execute('SELECT id, nimi, vedenpinta FROM ' + table)
				return db_info
			except Exception as e:
				logData("database_connect/fetchIds", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get id's from database"

	def fetchIds(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				db_ids = self.session.execute('SELECT id FROM ' + table)
				return db_ids
			except Exception as e:
				logData("database_connect/fetchIds", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get id's from database"

	def fetchWatersurface(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				watersurfaces = self.session.execute('SELECT vedenpinta FROM ' + table)
				return watersurfaces

			except Exception as e:
				logData("database_connect/fetchWatersurface", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get water surface level from database"

	def fetchRowcount(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				rows = self.session.execute('SELECT COUNT(*) FROM ' + table)

				return rows[0]

			except Exception as e:
				logData("database_connect/fetchRowcount", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get rowcount from database"

	def fetchName(self):
		if (self.connection == True):
			try:
				table = modl.getTable()

				names = self.session.execute('SELECT nimi FROM ' + table)
				return names
				
			except Exception as e:
				logData("database_connect/fetchName", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to get name from database"

	def deleteRow(self, c_id):
		if (self.connection == True):
			try:
				table = modl.getTable()
				delid = c_id

				if (self.connection == True):
					self.session.execute("DELETE FROM " + table + " WHERE id = " + delid + " IF EXISTS")
				else:
					print "Database Error: Failed to delete data in the database!"

			except Exception as e:
				logData("database_connect/deleteRow", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to delete row in database"

	def deleteManyRows(self, c_id, rowcount):
		if (self.connection == True):
			try:
				table = modl.getTable()
				delid = c_id
				i = 0

				while (i < rowcount[0]):
						self.session.execute("DELETE FROM " + table + " WHERE id = " + str(delid))

						delid = delid + 1
						i = i + 1

			except Exception as e:
				logData("database_connect/deleteManyRows", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to delete row in database"

	def sendMeterwellData(self, id_same, c_id, nimi, east, north, korkeus_merenpinnasta, lampotila, ominaissahkojohtavuus, paine, vedenpinta, virtausnopeus):
		if (self.connection == True):
			try:
				table = modl.getTable()

				# Update row if current id already exists or insert new id if it does not
				if (id_same == True):
					self.session.execute("UPDATE " + table + " SET nimi = (%s), east = (%s), north = (%s), korkeus_merenpinnasta = (%s)," \
										"lampotila = (%s), ominaissahkojohtavuus = (%s), paine = (%s), vedenpinta = (%s), virtausnopeus = (%s) " \
										"WHERE id = (%s)", (nimi, east, north, korkeus_merenpinnasta, lampotila, ominaissahkojohtavuus, paine, vedenpinta, virtausnopeus, c_id))
				elif (id_same == False):
					self.session.execute("INSERT INTO " + table + " (id, nimi, east, north, korkeus_merenpinnasta, " \
										"lampotila, ominaissahkojohtavuus, paine, vedenpinta, virtausnopeus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", \
										(c_id, nimi, east, north, korkeus_merenpinnasta, lampotila, ominaissahkojohtavuus, paine, vedenpinta, virtausnopeus))
				else:
					print "Database Error: Somethin's gone all wrong"

			except Exception as e:
				logData("database_connect/sendMeterwellData", str(e), False)
				print "Database Error: ", e
		else:
			print "Database Error: Failed to insert data to database!"

	# return the state of the database connection
	def getConnection(self):
			return self.connection

	# Close the database connection and set connection to false
	def closeConnection(self):
		if (self.connection == True):
			try:
				self.session.cluster.shutdown()
				self.session.shutdown()
				self.connection = False
				print "Connection closed"
			except Exception as e:
				logData("database_connect/closeConnection", str(e), False)
				print "Database Error: ", e
		else:
			print "Error: Failed to close database connection"