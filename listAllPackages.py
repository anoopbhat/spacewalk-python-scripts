#!/usr/bin/python
import sys, getpass, xmlrpclib,socket
from optparse import OptionParser

parser = OptionParser()

# Setup all the options we expect to get
parser.add_option("-s", "--server", dest="hostname", help="Spacewalk hostname or IP", metavar="hostname or IP")
parser.add_option("-u", "--username", dest="username", help="Spacewalk Username", metavar="username")
parser.add_option("-p", "--password", dest="password", help="Option password argument. if not provided, will be prompted for it.", metavar="password")
parser.add_option("-c", "--channel", dest="channel", help="Spacewalk channel", metavar="channel")
parser.add_option("-t", "--title", action="store_true", dest="printtitle")

(cfg, args) = parser.parse_args()

# validate the options and print errors or get more information from the user if needed
if not cfg.hostname:
	parser.error("Need a hostname. Try -s or --server")
else:
	spacewalkhost = "http://" + cfg.hostname + "/rpc/api"

if not cfg.username:
	parser.error("Need a username. Try -u or --username")

if not cfg.channel:
	parser.error("Need a channel name. Try -c or --channel")

if not cfg.password:
	cfg.password = getpass.getpass("Password: ")

client = xmlrpclib.Server(spacewalkhost, verbose=0)

# connect to the server and handle the most common exceptions
try:
        key = client.auth.login(cfg.username, cfg.password)
except xmlrpclib.Fault as err:
        print "ERROR: Code:{0}. String:{1}".format(err.faultCode, err.faultString)
        sys.exit()
except socket.error as (err, strerr):
	print "ERROR: {0}. Message:{1}".format(err, strerr)
	if err == 8:
		print "Seems like an invalid hostname? Try resolving it and then try again."
	sys.exit()

# list all the packages from the channel that was specified
list = client.channel.software.listAllPackages(key, cfg.channel)

# should we print a title row?
if cfg.printtitle == True:
        print "Package Version"

# print the package information
for package in list:
	print "{0} {1}".format(package.get('name'), package.get('version'))

# logout
client.auth.logout(key)

