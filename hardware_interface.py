import RPi.GPIO as GPIO
import board
import digitalio
import adafruit_dht
import psutil
import mh_z19
import time
from mcp3008 import MCP3008

#################################################################################################
# Global variables storing the references to the different sensors that are connected to the Pi #
#################################################################################################

# DHT11 sensors for measuring temperature and humidity
# Referenced using the CircuitPython board scheme in order to use the sensor objects produced by the Adafruit library
DHT_External  = adafruit_dht.DHT11(board.D25, use_pulseio = False)		
DHT_Internal1 =	adafruit_dht.DHT11(board.D23, use_pulseio = False)
DHT_Internal2 = adafruit_dht.DHT11(board.D24, use_pulseio = False)

Light_Sensing = 14

Fans = 17
Water_Valve = 27
Lights = 22

# Variables representing the states of the fans and LED lamp | 1 = on, 0 = off
Light_state = 0
Fan_state = 0
	
# ADC channels for analogue sensors
ADC = MCP3008()
Light_Channel =	0
Soil_Moisture =	1

##################################################################################
# Dictionary storing threshold values to activate/ deactivate relevent actuators #
##################################################################################

Threshold = {
	"Light_Threshold":		512,
	"Moisture_Threshold":	512,
	"Humidity_Threshold":	70.0,
	"Temp_Threshold":		24.0}

class hardware_interface:
	
	def __init__(self):
		self.Light_state = 0
		self.Fan_state = 0
		print("Hardware interface is initialized")
	
	##############################
	# Initializing the GPIO pins #
	##############################
	
	def initialize_GPIO(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		
		# Pin responsible for detecting the lighting control signal
		GPIO.setup(Light_Sensing, GPIO.IN)
		# Pins responsible for the control signals used for the relays
		GPIO.setup(Fans, GPIO.OUT, initial = GPIO.LOW) # Fans
		GPIO.setup(Water_Valve, GPIO.OUT, initial = GPIO.LOW) # Water valve
		GPIO.setup(Lights, GPIO.OUT, initial = GPIO.LOW) # LED Lamp
		
	
	####################################################### 
	# Methods that read the data of the different sensors #
	#######################################################
	
	#########################################
	# DHT11 Temperature and Humidity Sensor #
	#########################################
	
	# Note on DHT sensors:
	# DHT sensors have a tendency to cause a runtime errors on linux-based systems when retrieving sensor data
	# So, a 'try/ raise logic' needs to be used to retrieve the sensor data again after 2 seconds 
	
	# Gets the measured temperature from outside the greenhouse
	def get_external_temp(self):
		external_temp = 0
		
		while external_temp == 0:
			try:
				external_temp = DHT_External.temperature
			except RuntimeError as error:
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_External.exit()
				raise error
			
		return float(external_temp)	
	
	# Gets the measured temperatures of the 2 sensors from inside the greenhouse 	
	# Then returns the averaged result from the 2 sensors
	def get_internal_temp(self):
		temp1 = 0
		temp2 = 0
		
		while temp1 == 0:
			try:
				temp1 = DHT_Internal1.temperature 
			except RuntimeError as error:
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_Internal1.exit()
				raise error
				
		while temp2 == 0:
			try:
				temp2 = DHT_Internal2.temperature 
			except RuntimeError as error:
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_Internal2.exit()
				raise error
				
		return round((temp1 + temp2)/2, 2)
	
	# Gets the measured humidity from the 2 sensors inside the greenhouse
	# Then returns the averaged result from the 2 sensors		
	def get_humidity(self):
		hum1 = 0
		hum2 = 0
		
		while hum1 == 0:
			try:
				hum1 = DHT_Internal1.humidity 
			except RuntimeError as error:
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_Internal1.exit()
				raise error
				
		while hum2 == 0:
			try:
				hum2 = DHT_Internal2.humidity 
			except RuntimeError as error:
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_Internal2.exit()
				raise error
				
		return round((hum1 + hum2)/2, 2)	
	
	#####################
	# MH-Z19 CO2 Sensor #
	#####################
		
	# Gets the measured CO2 concentration inside the greenhouse
	# The value returned is in PPM (parts per million)
	def get_CO2(self):
		co2 = mh_z19.read_from_pwm(gpio = 12, range = 2000)
		return co2['co2']
	    	
	##################################
	# Light Dependent Resistor (LDR) #
	##################################
	
	# Broke the ADC now using the LDR as a switch using a potentiometer as a 'digital signal'
	# Sensitivity is adjusted with the pot
	# When the ambient lighting is sufficient the input pin will have read a high voltage
	# The input pin will read a low voltage when it's too dark
	def get_light_reading(self):
		if GPIO.input(Light_Sensing) == GPIO.LOW: # Lighting is low
			return 1
		elif GPIO.input(Light_Sensing) == GPIO.HIGH: # Lighting is high enough
			return 0
		
		# Gets the light reading from the LDR
		# The sensor data is read from the ADC 10 times then averaged to avoid inaccurate readings
		#Deprecated code as the ADC broke
		# light = 0
		
		# for i in range(10):
			# light += ADC.read(channel = Light_Channel)
			
		# return light/10
	
	########################################
	# Velleman VMA303 Soil Moisture Sensor #
	########################################
		
	# Gets the soil moisture reading
	# The sensor data is read from the ADC 10 times then averaged to avoid inaccurate readings
	def get_soil_moisture(self):
		moisture = 0
		
		for i in range(10):
			moisture += ADC.read(channel = Soil_Moisture)
		
		return moisture/10	
	
	###################################################
	# Methods that activate/ deactivate the actuators #
	###################################################
	
	############
	# LED Lamp #
	############
	
	def turn_light_on(self):
		GPIO.output(Lights, GPIO.HIGH)
		self.set_lighting_state(1)
		
	def turn_light_off(self):
		GPIO.output(Lights, GPIO.LOW)
		self.set_lighting_state(0)
	
	def set_lighting_state(self, state):
		if state == 1:
			self.Light_state = 1
		else:
			self.Light_state = 0
	
	def get_lighting_state(self):
		return self.Light_state
		
	################################
	# Normally Open Solenoid Valve #
	################################
	
	def water_plant(self):
		GPIO.output(Water_Valve, GPIO.HIGH)
		time.sleep(3)
		GPIO.output(Water_Valve, GPIO.LOW)
		
	#############################
	# Intake and Extractor Fans #
	#############################
	
	def turn_fans_on(self):
		GPIO.output(Fans, GPIO.HIGH)
		self.set_fan_state(1)
		
	def turn_fans_off(self):
		GPIO.output(Fans, GPIO.LOW)
		self.set_fan_state(0)
	
	def set_fan_state(self, state):
		if state == 1:
			self.Fan_state = 1
		else:
			self.Fan_state = 0
		
	def get_fan_state(self):
		return self.Fan_state
	
	###################################################
	# Methods that control the greenhouse environment #
	###################################################
	
	############
	# Lighting #
	############
	
	# Turns the light on if the ambient light is too low AND if the internal temperature isn't too high
	# Or turns the light off if the ambient light is good enough OR if the internal temperature is too high 
	def light_control(self):
		light_reading = self.get_light_reading()
		internal_temp = self.get_internal_temp()
		
		if light_reading == 1 and internal_temp <= (Threshold["Temp_Threshold"] + 2):
			self.turn_light_on() 
		elif light_reading == 0 or internal_temp > (Threshold["Temp_Threshold"] + 2):
			self.turn_light_off()
		# ADC broke
		# if light_reading <= Threshold["Light_Threshold"] and internal_temp <= (Threshold["Temp_Threshold"] + 5):
			# self.turn_light_on() 		
		# elif light_reading > Threshold["Light_Threshold"] or internal_temp > (Threshold["Temp_Threshold"] + 5):
			# self.turn_light_off()
			
	############
	# Watering #
	############
	
	# If the soil isn't wet enough, then the water valve is opened to water the plant
	def water_control(self):
		moisture_reading = self.get_soil_moisture()
		
		if moisture_reading >= Threshold["Moisture_Threshold"]:
			self.water_plant()
	
	# Unfortunetly the valve doesn't work due to the water pressure being too low to initialize itself
	
	###############
	# Ventilation #
	###############
	
	# Turns the fans on if the relative humidity is high enough to cause the water vapour to condense
	# Also turns the fans on if the internal temperature is too high 
	def ventilation(self):
		humidity = self.get_humidity()
		internal_temp = self.get_internal_temp()
		external_temp = self.get_external_temp()
		
		if humidity >= Threshold["Humidity_Threshold"]:
			self.turn_fans_on()	
		elif internal_temp >= Threshold["Temp_Threshold"] and internal_temp > external_temp:
			self.turn_fans_on()
		else:
			self.turn_fans_off()
		
