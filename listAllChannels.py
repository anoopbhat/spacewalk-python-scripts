#!/usr/bin/python
# I'm not particularly good at python. this is one of my first scripts.
# Please send tips/advice to anoop.bhat@gmail.com
# if you want to learn how to use the spacewalk api, simply go to About -> API
import sys, getpass, xmlrpclib,socket
from optparse import OptionParser

parser = OptionParser()

# Setup the options that we're expecting to get from the command line.
# -h not listed but automatically provides help usage info
parser.add_option("-s", "--server", dest="hostname", help="Spacewalk hostname or IP", metavar="hostname or IP")
parser.add_option("-u", "--username", dest="username", help="Spacewalk Username", metavar="username")
parser.add_option("-p", "--password", dest="password", help="Option password argument. if not provided, will be prompted for it.", metavar="password")
parser.add_option("-t", "--title", action="store_true", dest="printtitle")

# parse the arguments
(cfg, args) = parser.parse_args()

# print messages or get additional values based on the options provided or error and then exit.
if not cfg.hostname:
	parser.error("Need a hostname. Try -s or --server")
else:
	spacewalkhost = "http://" + cfg.hostname + "/rpc/api"

if not cfg.username:
	parser.error("Need a username. Try -u or --username")

# if -p is not provided, ask the user for a password. if it is, we're good.
if not cfg.password:
	cfg.password = getpass.getpass("Password: ")

client = xmlrpclib.Server(spacewalkhost, verbose=0)


# login to the server and catch any xmlrpclib faults or a socket error and handle that appropriately
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

# Get the list of channels from spacewlk
list = client.channel.listAllChannels(key)

# should we print a title row?
if cfg.printtitle == True:
	print "ID Label #Packages"

# list out all the channels and number of packages
for chan in list:
   print "{0} {1}".format(chan.get('id'), chan.get('label'), chan.get('packages'));

# logout of spacewalk
client.auth.logout(key)

