#!/usr/bin/env python

import mosquitto
from .util import *
import Queue
import time
import os

class Mqtt_client(object):
    """Main program class
    """
    def __init__(self, broker, port, qpub, qsub, name="pwmqtt", user = None, password = None):
        """
        ...
        """
        info("MQTT client initializing for " + str(broker) +":"+ str(port))
        self.broker = str(broker)
        self.port = str(port)
        self.qpub = qpub
        self.qsub = qsub
        self.rc = -1
        self.mqttc = None
        self.name = name+str(os.getpid())
        self.user = user
        self.password = password
        
        self.connect()
        debug("MQTT init done")
        
    def connected(self):
        return (self.rc == 0)
        
    def connect(self):
        self.mqttc = mosquitto.Mosquitto(self.name)
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_disconnect = self.on_disconnect
        self.mqttc.on_publish = self.on_publish
        self.mqttc.on_subscribe = self.on_subscribe
        
        #Set the username and password if any
        if self.user != None:
    	    self.mqttc.username_pw_set(self.user,self.password)
        
        return self._connect()

    def _connect(self):
        try:
            self.rc = self.mqttc.connect(self.broker, self.port, 60)
            info("MQTT connected return code %d" % (self.rc,))
            # if self.connected():
                # self.mqttc.subscribe("plugwise2py/cmd/#", 0)
                # info("MQTT subscribed to plugwise2py/cmd/#")
        except Exception as reason:
            error("MQTT connection error: "+str(reason))
        return self.rc
        
    def run(self):
        while True:
            while self.rc == 0:
                try:
                    self.rc = self.mqttc.loop()
                except Exception as reason:
                    self.rc = 1
                    error("MQTT connection error in loop: "+str(reason))
                    continue;
                #process data to be published
                while not self.qpub.empty():
                    data = self.qpub.get()
                    topic = data[0]
                    msg = data[1]
                    info(topic)
                    info(msg)
                    try:
                        self.mqttc.publish(topic, msg)
                    except Exception as reason:
                        error("MQTT connection error in publish: "+str(reason))
                time.sleep(0.1)
            error("MQTT disconnected")
            
            #attempt to reconnect
            time.sleep(5)
            self.rc = self._connect()
       
    def subscribe(self, topic, qos=0):
        if self.connected():
            self.mqttc.subscribe(topic, qos)
            info("MQTT subscribed to %s" % topic)

    def on_message(self, mosq, obj, msg):
        info("MQTT " + msg.topic+" "+str(msg.payload))
        self.qsub.put((msg.topic, str(msg.payload)))

    def on_connect(self, mosq, obj, rc):
        if rc == 0:
            info("MQTT connected return code 0")
        else:
            error("MQTT connected return code %d" % (self.rc,))
        self.rc = rc
            
    def on_disconnect(self, mosq, obj, rc):
        self.rc = rc
        info("MQTT disconnected (from on_disconnect)")

    def on_publish(self, mosq, obj, mid):
        debug("MQTT published message sequence number: "+str(mid))

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        info("MQTT Subscribed: "+str(mid)+" "+str(granted_qos))

    # def on_log(self, mosq, obj, level, string):
        # info(string)
