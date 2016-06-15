#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Class file for measurement locations

import math
import random
from data_format import *

class MeterWell(object):

	#Attributes
	wellid = None
	name = None
	# Sijainti
	eastloc = None
	northloc = None
	# Kaivon sijainti merenpinnasta
	well_level = None
	# Kaivon halkaisija
	well_diameter = None
	# Virtaustilavuus (tietokannassa virtausnopeus)
	flowrate = None
	# Vedenpinta
	watersurface = None
	# Lampotila
	temperature = None
	# Ominaissahkonjohtavuus
	conductivity = None
	# Paine
	pressure = None
	# Kaivoon tulevat virtaumat
	inc_flow_well = None
	# kaivosta lähtevat virtaumat
	out_flow_well = None
	# Incoming pipe diameter
	inc_pipe_d = 160.0/1000
	# Outgoing pipe diameter
	out_pipe_d = 160.0/1000
	# Incoming pipe length (x, y) (I, P)
	inc_pipe_loc = []
	# Outgoing pipe length (x, y) (I, P)
	out_pipe_loc = []

	#Constructor
	def __init__(self, wellid, name="", eastloc=1.0, northloc=1.0, well_level=0.0, inc_flow_well=0, out_flow_well=0, xi=0, yi=0, xo=0, yo=0):

		self.wellid = wellid
		self.name = name
		self.eastloc = eastloc
		self.northloc = northloc
		self.well_level = float(well_level)
		self.flowrate = 0.0
		self.watersurface = 0.0
		self.temperature = 0.0
		self.conductivity = 0.0
		self.pressure = 0.0
		self.inc_flow_well = inc_flow_well
		self.out_flow_well = out_flow_well
		self.inc_pipe_loc.extend([xi, yi])
		self.out_pipe_loc.extend([xo, yo])
		self.well_diameter = 0.8

		self.inc_pipe_d=0.2
		self.out_pipe_d=0.2

	#Methods

	# Getters & Setters
	def get_wellid(self):
		return self.wellid

	def get_name(self):
		return self.name

	def set_name(self, name):
		self.name = name

	def get_eastloc(self):
		return self.eastloc

	def set_eastloc(self, eastloc):
		self.eastloc = eastloc

	def get_northloc(self):
		return self.northloc

	def set_northloc(self, northloc):
		self.northloc = northloc

	def get_well_level(self):
		return self.well_level

	def set_well_level(self, well_level):
		self.well_level = well_level

	def get_flowrate(self):
		return self.flowrate

	def set_flowrate(self, flowrate):
		self.flowrate = flowrate

	def get_watersurface(self):
		return self.watersurface

	def set_watersurface(self, watersurface):
		self.watersurface = watersurface

	def get_temperature(self):
		return self.temperature

	def set_temperature(self, temperature):
		self.temperature = temperature

	def get_conductivity(self):
		return self.conductivity

	def set_conductivity(self, conductivity):
		self.conductivity = conductivity

	def get_pressure(self):
		return self.pressure

	def set_pressure(self, pressure1):
		self.pressure = pressure1

	def get_out_pipe_loc(self):
		return self.out_pipe_loc

	def set_out_pipe_loc(self, x, y):
		self.out_pipe_loc.append(x, y)

	def get_inc_pipe_loc(self):
		return self.inc_pipe_loc

	def set_inc_pipe_loc(self, x, y):
		self.inc_pipe_loc.append(x, y)

	def set_well_level(self, well_level):
		self.well_level = well_level

	def set_well_diameter(self, well_diameter):
		self.well_diameter = well_diameter

	# Measurement calculations

	# Counting a single flowrate, ha=starting height, hb=ending height
	def virtausnopeus(self, ha, hb, x):
		v = ha - hb
		k = self.kulmaprosentti(v, x)
		if (v<0): # if the subtraction is negative, we're dealing with a pressure pipe
			if (0<k and 25>=k):
				return int(random.randrange(7, 8))/10
			if (25<k and 50>=k):
				return int(random.randrange(9, 10))/10
			if (50<k and 75>=k):
				return int(random.randrange(11, 12))/10
			else:
				return 1.3  
		else: # if the subtraction is positive, we're dealing with a flow pipe
			if (0<k and 33>=k):
				return int(random.randrange(4, 5))/10
			if (33<k and 66>=k):
				return int(random.randrange(6, 7))/10
			else:
				return 0.8

    # Counting the angle from 90 degrees
	def kulmaprosentti(self, v, x):
		if (0>v):
			neg = -1
			pro = neg * v
			y = 90 - pro
		else:
			y = v
		z = y / x
		c = math.atan(z)
		k = math.degrees(c)
		p = k/90
		pro = p*100
		j = int(pro)
		return j

    # Calculating the distance used as a reference, Ia=x, Ib=x, Pa=y, Pb=y
	def etaisyys(self, Ia, Ib, Pa, Pb):
		I=Ia-Ib
		P=Pa-Pb
		return math.sqrt(I*I+P*P)

    # Height of the waters surface, t=time, r=diameter of the pipe, v=volume flow rate
	def pinta(self, t, r, v):
		pii = math.pi
		x = v * t
		y = pii * r * r
		h = x / y

		return h

	# Push from the well, h=height difference from the fluid surface of the highest well
	def tyonto(self):
		h = self.watersurface
		if(0<h):
			g = 9.81
			q = int(random.randrange(4, 5))/10
			y = q*g*h
			y = y*100
			x = int(math.sqrt(y))
			x = x/100

			log_data("Measurement_location/tyonto", "Q: " + str(q) + ", Y: " + str(y) + ", X: " + str(x), False)

			if (0.3<x):
				self.pressure = 0.3
			else:
				self.pressure = x
		else:
			return 0

    #Volumetric flow rate, d=pipe diameter, v=flow velocity
	def virtaustilavuus(self, d, v):
		pii = math.pi
		z = pii*d*d*v
		return z/4

	def countWaterLevel(self, t, f, fu, last):

		# Incoming pipes length
		xa = self.etaisyys(self.inc_pipe_loc[0], self.inc_pipe_loc[1], self.eastloc, self.northloc)
		xb = self.etaisyys(self.eastloc, self.northloc, self.out_pipe_loc[0], self.out_pipe_loc[1])

		a = self.well_level
		d = self.well_diameter
		c = self.inc_flow_well
		b = self.out_flow_well

		# Incoming flows to the well
		if (c == 0):
			sisaan_v = float(random.randrange(7, 13))/10
			log_data("Measurement_location/countWaterLevel", "sisaan_v: " + str(sisaan_v), False)
		else:
			koulu = int(random.randrange(0, 5))/10
			sisaan_v = self.virtausnopeus(c,a,xa) + fu + koulu
			log_data("Measurement_location/countWaterLevel", "sisaan_v: " + str(sisaan_v) + ", former_pressure: " + str(fu), False)

		tilavuus_sisaan = float(self.virtaustilavuus(self.inc_pipe_d, sisaan_v))
		# Outgoing flows from the well
		if (b > 0):
			ulos_v = self.virtausnopeus(a, b, xb)+f
			tilavuus_ulos = float(self.virtaustilavuus(self.out_pipe_d, ulos_v))

		# Water surface level
		if (b > 0):
			self.flowrate = tilavuus_sisaan - tilavuus_ulos
		else:
			self.flowrate = tilavuus_sisaan
		r = d/2
		muutos = float(self.pinta(t, r, self.flowrate))
		syvyys = self.watersurface + muutos

		log_data("Measurement_location/countWaterLevel", "Pressure: " + str(self.pressure) + ", Flowrate: " + str(self.flowrate), False)

		if (last == True):
			if (syvyys < 0):
				self.watersurface = 0
			elif (syvyys > 0 and 2.2 >= syvyys):
				self.watersurface = syvyys
			else:
				self.watersurface = 2.2
		else:
			if (0 < syvyys):
				self.watersurface = syvyys
			else:
				self.watersurface = 0