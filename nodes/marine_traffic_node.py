#!/usr/bin/env python

import rospy
from geographic_msgs.msg import GeoPointStamped
from project11_msgs.msg import Contact

from dynamic_reconfigure.server import Server
from marine_traffic_com.cfg import marine_traffic_comConfig

from project11 import geodesic
import urllib2
import math
import json
import dateutil.parser
import calendar

position = None

lastQueryTime = rospy.Time()
enabled = False
queryDistance = 10000

n_rad = 0
e_rad = math.radians(90)
s_rad = math.radians(180)
w_rad = math.radians(270)

api_entry_point = 'https://services.marinetraffic.com/api/exportvessels/v:8'

'''
From: https://www.marinetraffic.com/en/ais-api-services/documentation/api-service:ps06

Typical API call:
https://services.marinetraffic.com/api/exportvessels/v:8/YOUR-API-KEY/MINLAT:value/MAXLAT:value/MINLON:value/MAXLON:value/timespan:#minutes/protocol:value

Example API call:
https://services.marinetraffic.com/api/exportvessels/v:8/8205c862d0572op1655989d939f1496c092ksvs4/MINLAT:38.20882/MAXLAT:40.24562/MINLON:-6.7749/MAXLON:-4.13721/timespan:10/protocol:json
'''

'''
[{"MMSI":"367148830","IMO":"0","SHIP_ID":"438387","LAT":"45.504950","LON":"-83.855960","SPEED":"67","HEADING":"299","COURSE":"297","STATUS":"99","TIMESTAMP":"2019-05-08T17:41:24","DSRC":"TER","UTC_SECONDS":"10","SHIPNAME":"CHAMPION","SHIPTYPE":"91","CALLSIGN":"WDD4771","FLAG":"US","LENGTH":"24","WIDTH":"7","GRT":"","DWT":"","DRAUGHT":"0","YEAR_BUILT":"","ROT":"0","TYPE_NAME":"Other","AIS_TYPE_SUMMARY":"Other","DESTINATION":"CHEBOYGAN MI","ETA":""},{"MMSI":"369970364","IMO":"0","SHIP_ID":"457434","LAT":"45.539720","LON":"-83.639290","SPEED":"61","HEADING":"511","COURSE":"108","STATUS":"99","TIMESTAMP":"2019-05-08T17:20:07","DSRC":"TER","UTC_SECONDS":"7","SHIPNAME":"NOAA R 5002 STORM","SHIPTYPE":"37","CALLSIGN":"","FLAG":"US","LENGTH":"0","WIDTH":"0","GRT":"","DWT":"","DRAUGHT":"0","YEAR_BUILT":"","ROT":"0","TYPE_NAME":"Pleasure Craft","AIS_TYPE_SUMMARY":"Pleasure Craft","DESTINATION":"CLASS B","ETA":""}]
'''

def positionCallback(data):
    global position
    position = data.position
    #print enabled, queryDistance
    getContacts()

def getContacts():
    global lastQueryTime
    if enabled:
        now = rospy.Time.now()
        if now-lastQueryTime > rospy.Duration.from_sec(120):
            if position is None:
                print 'no position'
            else:
                lastQueryTime = now
                print 'looking for data...'
                print 'range:', queryDistance
                print position
                lat_rad = math.radians(position.latitude)
                lon_rad = math.radians(position.longitude)
                
                n_position = geodesic.direct(lon_rad,lat_rad,n_rad,queryDistance)
                e_position = geodesic.direct(lon_rad,lat_rad,e_rad,queryDistance)
                s_position = geodesic.direct(lon_rad,lat_rad,s_rad,queryDistance)
                w_position = geodesic.direct(lon_rad,lat_rad,w_rad,queryDistance)
                max_lat = math.degrees(n_position[1])
                min_lat = math.degrees(s_position[1])
                min_lon = math.degrees(w_position[0])
                max_lon = math.degrees(e_position[0])
                print min_lat,max_lat,min_lon,max_lon
                
                query_parts = [api_entry_point, api_key]
                query_parts.append('MINLAT:'+str(min_lat))
                query_parts.append('MAXLAT:'+str(max_lat))
                query_parts.append('MINLON:'+str(min_lon))
                query_parts.append('MAXLON:'+str(max_lon))
                query_parts.append('msgtype:extended')
                query_parts.append('protocol:jsono')
                
                query = '/'.join(query_parts)
                #print query
                request = urllib2.Request(query,headers = {'User-Agent': 'Mozilla/5.0'})
                contacts = urllib2.urlopen(request).read()
                for contact in json.loads(contacts):
                    print contact
                    c = Contact()
                    ts = dateutil.parser.parse(contact['TIMESTAMP'])
                    print ts
                    c.header.stamp = rospy.Time.from_sec(calendar.timegm(ts.timetuple()))
                    c.contact_source = 1
                    c.mmsi = int(contact['MMSI'])
                    c.name = contact['SHIPNAME']
                    c.callsign = contact["CALLSIGN"]
                    c.position.latitude = float(contact['LAT'])
                    c.position.longitude = float(contact['LON'])
                    c.cog = float(contact['COURSE'])
                    c.sog = float(contact['SPEED'])/10.0
                    c.heading = float(contact['HEADING'])
                    c.dimension_to_stbd = float(contact['WIDTH'])/2.0
                    c.dimension_to_port = float(contact['WIDTH'])/2.0
                    c.dimension_to_bow = float(contact['LENGTH'])/2.0
                    c.dimension_to_stern = float(contact['LENGTH'])/2.0
                    contact_pub.publish(c)
            
 
def reconfigure_callback(config, level):
    global enabled
    global queryDistance
    global lastQueryTime
    if not enabled and config['enable']:
        lastQueryTime = rospy.Time() #resets timer
    enabled = config['enable']
    queryDistance = config['query_distance']
    return config


rospy.init_node('marine_traffic_com')
rospy.Subscriber('/udp/position', GeoPointStamped, positionCallback)
contact_pub = rospy.Publisher('/udp/contact', Contact, queue_size=10)

api_key = rospy.get_param('/marine_traffic_com/api_key')

config_server = Server(marine_traffic_comConfig, reconfigure_callback)

rospy.spin()
