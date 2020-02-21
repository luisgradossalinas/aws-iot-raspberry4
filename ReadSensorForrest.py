import time
import os
import base64
from time import sleep
import uuid
import json
import sys
import datetime
import RPi.GPIO as GPIO
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

def payload_report(self, params, packet):
    print("----- New Payload -----")
    print("Topic: ", packet.topic)
    print("Message: ", packet.payload)
    print("-----------------------")

certRootPath = '/home/pi/projects-iot/forrest/'
print("Iniciando maraton")

aws_endpoint = "a27xxoa1dbt45wz-atx.iot.us-east-1.amazonaws.com"
aws_port = 8883
# Unique ID. If another connection using the same key is opened the previous one is auto closed by AWS IOT
mqtt_client = AWSIoTMQTTClient("raspi4") 
#Used to configure the host name and port number the underneath AWS IoT MQTT Client tries to connect to.
mqtt_client.configureEndpoint(aws_endpoint, aws_port)
# Used to configure the rootCA, private key and certificate files. configureCredentials(CAFilePath, KeyPath='', CertificatePath='')
mqtt_client.configureCredentials(certRootPath + "Amazon_Root_CA_1.pem", certRootPath + "d153f2c936-private.pem.key", certRootPath + "d153f2c936-certificate.pem.crt")
# Configure the offline queue for publish requests to be 20 in size and drop the oldest
mqtt_client.configureOfflinePublishQueueing(-1)
# Used to configure the draining speed to clear up the queued requests when the connection is back. (frequencyInHz)
mqtt_client.configureDrainingFrequency(2) 
# Configure connect/disconnect timeout to be 10 seconds
mqtt_client.configureConnectDisconnectTimeout(10)
# Configure MQTT operation timeout to be 5 seconds
mqtt_client.configureMQTTOperationTimeout(5)
# Connect to AWS IoT with default keepalive set to 600 seconds
mqtt_client.connect()
# Subscribe to the desired topic and register a callback.
mqtt_client.subscribe("raspi4/payload_test", 1, payload_report)

try:
	GPIO.setmode(GPIO.BOARD)

	PIN_TRIGGER = 7
	PIN_ECHO = 11
	GPIO.setup(PIN_TRIGGER, GPIO.OUT)
	GPIO.setup(PIN_ECHO, GPIO.IN)

	i = 0
	while True:

		GPIO.output(PIN_TRIGGER, GPIO.LOW)

    #Cada medio segundo revisa la distancia entre Forrest y la meta
		time.sleep(0.5)

		print("Calculando la distancia de Forrest a la meta")

		GPIO.output(PIN_TRIGGER, GPIO.HIGH)

		time.sleep(0.00001)

		GPIO.output(PIN_TRIGGER, GPIO.LOW)

		while GPIO.input(PIN_ECHO) == 0:
			pulse_start_time = time.time()
		while GPIO.input(PIN_ECHO) == 1:
			pulse_end_time = time.time()

		pulse_duration = pulse_end_time - pulse_start_time
		distance = round(pulse_duration * 17150, 2)
		print("Distancia: %.1f cm" % distance)

		fecha = datetime.datetime.now()
    
		i = i + 1
		print('Publishing to "raspi4/forrest" the value: ', i)
		message = {}
		message['cont'] = i
		message['date_reg'] = str(fecha)
		message['value_sensor'] = round(distance,1)
		message['name'] = "Forrest Gump"
		messageJson = json.dumps(message)
		mqtt_client.publish("raspi4/forrest", messageJson, 0)

		sleep(0.5)

    #Si llega a la meta
		if float(distance) < float(5):
			print("Felicitaciones Forrest llegaste a la meta")
			break

		time.sleep(0.5)

finally:
	GPIO.cleanup()
