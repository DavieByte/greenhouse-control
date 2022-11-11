import argparse 
import psutil
import time
import matplotlib.pyplot as plt
import numpy as np
from hardware_interface import hardware_interface


if __name__ == '__main__':
	# Checking if the libgpiod process is running, and kill it if it is
	for proc in psutil.process_iter():
		if proc.name() == 'libgpiod_pulsein' or proc.name() == 'libgpiod_pulsei':
			proc.kill()
	
	# hardware_interface object instance that allows the program to interface with the sensors and actuators of the system
	component = hardware_interface()
	
	# Initializes the GPIO pins for operation
	component.initialize_GPIO()
	
	######################################
	# Setting up the commandline parsers #
	######################################
	
	# When -h or --help is entered or when no argument is entered
	parser = argparse.ArgumentParser(description = 'Run the default greenhouse control algorithm or run the different testing procedures for the greehouse or test the sensors and actuators by using the commandline arguments shown below:')
	
	# defining the different commandline arguments
	parser.add_argument('-r','--run', action = 'store_true', help = 'Greenhouse environmental control operation')
	parser.add_argument('-ct', '--control', action = 'store_true', help = 'Tests the environmental control capability of the greenhouse')
	parser.add_argument('-ht', '--heating', action = 'store_true', help = 'Tests the heating capability of the LED lamp')
	parser.add_argument('-vt', '--ventilation', action = 'store_true', help = 'Tests how the ventilation of the greenhouse influences the environment')
	parser.add_argument('-d', '--display', action = 'store_true', help = 'Displays the current sensor data of the greenhouse environment')
	parser.add_argument('-l', '--lights', action = 'store_true', help = 'Turns the LED lamp on then off after 10 seconds')
	parser.add_argument('-w', '--water', action = 'store_true', help = 'Opens the water valve for 2 seconds')
	parser.add_argument('-f', '--fans', action = 'store_true', help = 'Turns the fans on then off after 10 seconds')

	
	################################################################
	# Different modes of operations based on commandline arguments #
	################################################################
	
	args = parser.parse_args()	
	
	###################################
	# Environmental Control Algorithm #
	###################################
	
	# Runs the intended greenhouse environmental control algorithm
	# The system will operate for 12 hours then go on standby for another 12 hours
	# During the operational time the program will continuously read data from the sensors and will decide which actuators to activate/ deactivate to control the greenhouse environment within the acceptable parameters
	# Sensor data will be displayed once every 10 iterations of the control loop
	if args.run:
		while True:
			# System in operation for 12 hours
			duration = time.time() + 12*60*60
			iteration = 0
			while time.time() < duration:
				# Displaying current sensor data
				if iteration == 10:
					print("External Temperature: " + str(component.get_external_temp()) + " *C \n" +
						  "Internal Temperature: " + str(component.get_internal_temp()) + " *C \n" +	
						  "Relative Humidity: " + str(component.get_humidity()) + " % \n" + 
						  "CO2 Concentration: " + str(component.get_CO2()) + " ppm \n" + 
						  "Lighting State: " + str(component.get_light_reading()) +  "\n" +
						  "Soil Moisture State: " + str(component.get_soil_moisture()*100/1024) + "%")
					iteration = 0
				
				# Control loop
				component.light_control()
				component.ventilation()
				# Unfortunetly the valve doesn't work due to the water pressure being too low to initialize itself
				# component.water_control()
				time.sleep(5)
				iteration += 1
			
			# Turns off any GPIO pins as they are not in use 
			GPIO.cleanup()
			# System goes on standy for 12 hours	
			time.sleep(12*60*60)
			# Refreshes the GPIO pins to be ready for operation
			component.initialize_GPIO()
					
	##############################
	# Environmental Control Test #
	##############################
	
	# Tests the environmental control capability of the system
	# The system will remain active for 30 minutes where sensors data will influence the activation of the actuators within the duration
	# Sensor data will be recorded for the 30 minute duration
	if args.control:
		# Clearning any pre-existing file data
		clearing_ec_log = open("environmental_control_log.csv", "w")
		clearing_ec_log.close()
		
		# Opening log file to append testing data
		ec_log = open("environmental_control_log.csv", "a")
		ec_log.write("Sample #, External Temperature, Internal Temperature, Relative Humidity, CO2 Concentration, Lighting, Soil Moisture, Lighting State, Fan State \n")
		
		# Initializing storage variables
		readings = 0
		external_temp_readings = []
		internal_temp_readings = []
		relative_humidity_readings = []
		co2_concentration_readings = []
		lighting_percentage_readings = []
		soil_moisture_percentage_readings = []
		lighting_states = []
		fan_states = []
		
		# Obtaining test data
		print("Starting Environmental Control Test")
		duration = time.time() + 60*30
		while time.time() < duration:
			# Capturing sensor data
			e_temp = component.get_external_temp()
			i_temp = component.get_internal_temp()
			hum = component.get_humidity()
			co2 = component.get_CO2()
			lighting = int(component.get_light_reading())
			moisture = (component.get_soil_moisture()/1024)*100 # ADC reading as percentage
			l_state = component.get_lighting_state()
			f_state = component.get_fan_state()
			
			
			external_temp_readings.append(e_temp)
			internal_temp_readings.append(i_temp)
			relative_humidity_readings.append(hum)
			co2_concentration_readings.append(co2)
			lighting_percentage_readings.append(lighting)
			soil_moisture_percentage_readings.append(moisture)
			lighting_states.append(l_state)
			fan_states.append(f_state)
			
			# Writing sensor data to log
			sensor_output = str(readings) + "," + str(e_temp) + "," + str(i_temp) + "," + str(hum) + "," + str(co2) + "," + str(lighting) + "," + str(moisture) + "," + str(l_state) + "," + str(f_state) + "\n"
			ec_log.write(sensor_output)
			
			readings += 1
			
			# Displays sensor data periodically
			if readings % 5 == 0:
				print(sensor_output)
			
			# Control loop
			component.light_control()
			component.ventilation()
			# Unfortunetly the valve doesn't work due to the water pressure being too low to initialize itself
			# component.water_control() 
			
			time.sleep(5)
		
		ec_log.close()
		component.turn_fans_off()
		component.turn_light_off()	
		print("Environmental control test is complete")
		
		# Displaying the test results as multiple plots	
		samples = np.arange(0, readings, 1)	
		
		# External temperature plot
		e_temp_fig = plt.figure("External Temperature Figure")
		plt.plot(samples, external_temp_readings)
		plt.xlabel('Samples')
		plt.ylabel('Temperature (*C)')
		plt.title('Environmental Control Test: External Temperature Readings')
		plt.savefig('Environmental Control Test: External Temperature Readings.png')	
		
		# Internal temperature plot
		i_temp_fig = plt.figure("Internal Temperature Figure")
		plt.plot(samples, internal_temp_readings)
		plt.xlabel('Samples')
		plt.ylabel('Temperature (*C)')
		plt.title('Environmental Control Test: Internal Temperature Readings')
		plt.savefig('Environmental Control Test: Internal Temperature Readings.png')	
		
		# Relative Humidity plot
		rh_fig = plt.figure("Relative Humidity Figure")
		plt.plot(samples, relative_humidity_readings)
		plt.xlabel('Samples')
		plt.ylabel('Relative Humidity (%)')
		plt.title('Environmental Control Test: Relative Humidity Readings')
		plt.savefig('Environmental Control Test: Relative Humidity Readings.png')
		
		# CO2 Concentration plot
		co2_fig = plt.figure("CO2 Concentration Figure")
		plt.plot(samples, co2_concentration_readings)
		plt.xlabel('Samples')
		plt.ylabel('CO2 Concentration (ppm)')
		plt.title('Environmental Control Test: CO2 Concentration Readings')
		plt.savefig('Environmental Control Test: CO2 Concentration Readings.png')
		
		# Ambient Lighting plot
		lighting_fig = plt.figure("Ambient Lighting Figure")
		plt.plot(samples, lighting_percentage_readings)
		plt.xlabel('Samples')
		plt.ylabel("Ambient Lighting State")
		plt.title('Environmental Control Test: Ambient Lighting Readings')
		plt.savefig('Environmental Control Test: Lighting Readings.png')
		
		# Soil Moisture plot
		sm_fig = plt.figure("Soil Moisture Figure")
		plt.plot(samples, soil_moisture_percentage_readings)
		plt.xlabel('Samples')
		plt.ylabel('Soil Moisture (%)')
		plt.title('Environmental Control Test: Soil Moisture Readings')
		plt.savefig('Environmental Control Test: Soil Moisture Readings.png')
		
		# Lighting State plot
		ls_fig = plt.figure('Lighting States Figure')
		plt.plot(samples, lighting_states)
		plt.xlabel('Samples')
		plt.ylabel('Lighting State')
		plt.title('Environmental Control Test: Lighting States Readings')
		plt.savefig('Environmental Control Test: Lighting States.png')
		
		# Fans State plot
		fs_fig = plt.figure('Fans States Figure')
		plt.plot(samples, fan_states)
		plt.xlabel('Samples')
		plt.ylabel('Fans State')
		plt.title('Environmental Control Test: Fans States Readings')
		plt.savefig('Environmental Control Test: Fans States.png')
		
		plt.show()
	
	#########################
	# LED Lamp Heating Test #
	#########################
	
	# Testing the heating capability of the LED lamp by turning it on for 30 minutes and recording the temperature data for the duration
	if args.heating:
		# Clearning any pre-existing file data
		clearing_lamp_heating_log = open("lamp_heating_log.csv", "w")
		clearing_lamp_heating_log.close()
		
		# Opening log file to append testing data
		lamp_heating_log = open("lamp_heating_log.csv", "a")
		lamp_heating_log.write("Sample #, Temperature \n")
		
		# Initializing storage variables
		temperature_readings = []
		readings = 0
		
		# Obtaining test data
		duration = time.time() + 60*30
		component.turn_light_on()
		while time.time() < duration:
			temp = component.get_internal_temp()
			temperature_readings.append(temp)
			output = str(readings) + "," + str(temp) + "\n"
			lamp_heating_log.write(output)
			time.sleep(2)
			readings += 1
			
			if readings % 10 == 0:
				print(output)

		lamp_heating_log.close()
		component.turn_light_off()
		print("LED lamp heating test is complete")
		
		# Displaying the test data as a graph
		samples = np.arange(0, readings, 1)
		plt.plot(samples, temperature_readings)
		plt.xlabel('Samples')
		plt.ylabel('Temperature (*C)')
		plt.title('LED Lamp Heating Test')
		plt.savefig('LED Lamp Heating Test.png')
		plt.show()
		
	####################
	# Ventilation Test #
	####################
	
	# Testing the ventilation of the system by turning the fans on for 30 minutes
	# External temperature (*C), internal temperature (*C), relative humidity (%), and CO2 concentration (in PPM) is recorded from the sensor readings
	if args.ventilation:
		# Clearning any pre-existing file data
		clear_ventilation_log = open("ventilation_log.csv", "w+")
		clear_ventilation_log.close()

		# Initializing arrays that store the test variables
		external_temp = []
		internal_temp = []
		humidity = []
		co2_concentration = []
		
		readings = 0
		
		# Opening log file to append testing data
		ventilation_log = open("ventilation_log.csv", "a")
		ventilation_log.write("Sample #, External Temperature, Internal Temperature, Relative Humidity, CO2 concentration \n")
		
		# Obtaining test data
		duration = time.time() + 60*30
		component.turn_fans_on()
		while time.time() < duration:
			e_temp = component.get_external_temp()
			i_temp = component.get_internal_temp()
			hum = component.get_humidity()
			co2 = component.get_CO2()
			
			external_temp.append(e_temp)
			internal_temp.append(i_temp)
			humidity.append(hum)
			co2_concentration.append(co2)
			
			output = str(readings) + "," + str(e_temp) + "," + str(i_temp) + "," + str(hum) + "," + str(co2) + " \n"
			ventilation_log.write(output)
		
			readings += 1
			time.sleep(2)
			
			if readings % 10 == 0:
				print(output)
			
		ventilation_log.close()
		component.turn_fans_off()
		print("Ventilation Test is complete")

		# Displaying the test results as multiple plots
		samples = np.arange(0, readings, 1)
		
		fig = plt.figure()		
		fig.suptitle("Ventilation Test")
		
		# External and internal temperature plot
		ax1 = fig.add_subplot(121)
		ax1.set(title = 'Temperature Readings', xlabel = 'Samples', ylabel = 'Temperature (*C)')
		external_t, = ax1.plot(samples, external_temp, 'r', label = 'External Temperature')
		internal_t, = ax1.plot(samples, internal_temp, 'b', label = 'Internal Temperature')
		
		# Relative humidity plot
		ax2 = fig.add_subplot(222)
		ax2.set(title = 'Relative Humidity Readings', xlabel = 'Samples', ylabel = 'Relative Humidity (%)')
		ax2.plot(samples, humidity) 
		
		# CO2 concentration plot
		ax3 = fig.add_subplot(224)
		ax3.set(title = 'CO2 Concentration Readings', xlabel = 'Samples', ylabel = 'CO2 Concentration (ppm)')
		ax3.plot(samples, co2_concentration) 

		plt.tight_layout(pad = 1)
		plt.savefig('Ventilation Test.png')
		plt.show()
		
	# Displays the current sensor data 	
	if args.display:
		print("External Temperature: " + str(component.get_external_temp()) + " *C \n" +
			  "Internal Temperature: " + str(component.get_internal_temp()) + " *C \n" +	
			  "Relative Humidity: " + str(component.get_humidity()) + " % \n" + 
			  "CO2 Concentration: " + str(component.get_CO2()) + " ppm \n" + 
			  "Lighting State: " + str(component.get_light_reading()) + "\n" + #str(round(((component.get_light_reading()/1024)*100))) + "% \n" +
			  "Soil Moisture State: " + str(round(((component.get_soil_moisture()/1024)*100))) + "%")

	# Turns the LED lamp on for 10 seconds
	if args.lights:
		component.turn_light_on()
		
		for i in range(10):
			print(10 - i)
			time.sleep(1)
		
		component.turn_light_off()
	
	# Opens the water valve for 2 seconds	
	if args.water:
		component.water_plant()

	# Turn the fans on for 10 seconds	
	if args.fans:
		component.turn_fans_on()
		
		for i in range(10):
			print(10 - i)
			time.sleep(1)
			
		component.turn_fans_off()

