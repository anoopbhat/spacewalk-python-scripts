#!/usr/bin/python

# This script ideally will validate checksums of packages between two servers.
# I find this particularly useful to run from time to time to find out which 
# packages on my source (or test) spacewalk server don't match what i have in production!
# -h will automatically print the help/usage information

import sys, getpass, xmlrpclib,socket
from optparse import OptionParser

parser = OptionParser()

# Setup all the options we expect to get for the source spacewalk server
parser.add_option("--ss", "--srchost", dest="srchost", help="Source spacewalk server or IP", metavar="srchostname")
parser.add_option("--su", "--srcuser", dest="srcuser", help="Source spacewalk username", metavar="srcuser")
parser.add_option("--sp", "--srcpass", dest="srcpass", help="Optional source spacewalk user password. If not provided, will be prompted", metavar="srcuserpass")
parser.add_option("--sc", "--srcchannel", dest="srcchannel", help="Source spacewalk channel label", metavar="srcchannel")

# Setup all the options we expect to get for the destinaction spacewalk server
parser.add_option("--ds", "--dsthost", dest="dsthost", help="Source spacewalk server or IP", metavar="dsthostname")
parser.add_option("--du", "--dstuser", dest="dstuser", help="Source spacewalk username", metavar="dstuser")
parser.add_option("--dp", "--dstpass", dest="dstpass", help="Optional source spacewalk user password. If not provided, will be prompted", metavar="dstuserpass")
parser.add_option("--dc", "--dstchannel", dest="dstchannel", help="Source spacewalk channel label", metavar="dstchannel")

# options on what to print all or just the bad ones
parser.add_option("-v", "--verbose", action="store_true", dest="verbosity", help="If set will print everything. If not, just the packages that do not match between source and destination")

(cfg, args) = parser.parse_args()

# validate the source server options
if not cfg.srchost:
	parser.error("Need a source hostname or IP Please. Try --ss or --srchost")
else:
	srcspacewalkhost = "http://" + cfg.srchost + "/rpc/api"

if not cfg.srcuser:
	parser.error("Need a source server username that can login. Try --su or --srcuser")

if not cfg.srcpass:
	cfg.srcpass = getpass.getpass("Password for " + cfg.srcuser + " on " + cfg.srchost + ": ")

if not cfg.srcchannel:
	parser.error("Need a source server channel name. Try --sc or --srcchannel. Also try listAllChannels.py from the same repo for a list of channels")

# validaet the destination server options
if not cfg.dsthost:
        parser.error("Need a source hostname or IP Please. Try --ds or --dsthost")
else:
        dstspacewalkhost = "http://" + cfg.dsthost + "/rpc/api"

if not cfg.dstuser:
        parser.error("Need a source server username that can login. Try --du or --dstuser")

if not cfg.dstpass:
        cfg.dstpass = getpass.getpass("Password for " + cfg.dstuser + " on " + cfg.dsthost + ": ")

if not cfg.dstchannel:
        parser.error("Need a source server channel name. Try --dc or --dstchannel. Also try listAllChannels.py from the same repo for a list of channels")

# ok we should have all the options all setup now
srcclient = xmlrpclib.Server(srcspacewalkhost, verbose=0, allow_none=True)
dstclient = xmlrpclib.Server(dstspacewalkhost, verbose=0, allow_none=True)

# if there are any packages that do not match, we should put them in a list and print those out at the end
invalidpkglist = list()

# connect to the source server and handle the most common exceptions
try:
        srckey = srcclient.auth.login(cfg.srcuser, cfg.srcpass)
except xmlrpclib.Fault as err:
        print "Error connecting to {0} as {1}: Code:{2}. String:{3}".format(cfg.srchost, cfg.srcuser, err.faultCode, err.faultString)
        sys.exit()
except socket.error as (err, strerr):
        print "Socket error connectiong to {0}: {1}. Message:{2}".format(cfg.dsthost, err, strerr)
	if err == 8:
		print "Seems like an invalid hostname? Try resolving it and then try again."
	sys.exit()

# connect to the dest server and handle the most common exceptions
try:
	dstkey = dstclient.auth.login(cfg.dstuser, cfg.dstpass)
except xmlrpclib.Fault as err:
        print "Error connecting to {0} as {1}: Code:{2}. String:{3}".format(cfg.dsthost, cfg.dstuser, err.faultCode, err.faultString)
        sys.exit()
except socket.error as (err, strerr):
        print "Socket error connectiong to {0}: {1}. Message:{2}".format(cfg.dsthost, err, strerr)
        if err == 8:
                print "Seems like an invalid hostname? Try resolving it and then try again."
        sys.exit()


# list all the packages from the channel that was specified
try: 
	srcpkglist = srcclient.channel.software.listAllPackages(srckey, cfg.srcchannel)
except xmlrpclib.Fault as err:
	print "Error getting list of packages from {0}. Code: {1}. Message: {2}".format(cfg.srchost, err.faultCode, err.faultString)
	sys.exit()

# here's where we check the checksum and display any mismatches or if the package just doesn't exist.
for package in srcpkglist:
	
	# collect information about packages from the source
	srcpkgname = package.get('name')
	srcpkgversion = package.get('version')
	srcpkgrelease = package.get('release')
	srcpkgchecksum = package.get('checksum')
	srcpkgarch = package.get('arch_label')

	# search for each individual package on the destination side and pull out the id
	try:
		dstpkgresults = dstclient.packages.findByNvrea(dstkey, srcpkgname, srcpkgversion, srcpkgrelease, "", srcpkgarch)
	except xmlrpclib.Fault as err:
       		print "Error searching for package {0}-{1} from {2}. Code: {3}. Message: {4}".format(srcpkgname, srcpkgversion, cfg.dsthost, err.faultCode, err.faultString)
		sys.exit()

	# dstpkgresults is a list with a dictionary so we must pop off the list and then use the .get method
	dstpkgid = dstpkgresults.pop().get('id')


	# try to get the details of the package we just searched for
	try:
		dstpkginfo = dstclient.packages.getDetails(dstkey, dstpkgid)
        except xmlrpclib.Fault as err:
                print "Error getting package information for {0} from {1}. Code: {2}. Message: {3}".format(dstpkgid, cfg.dsthost, err.faultCode, err.faultString)
                sys.exit()

	# collect information about the package so we can compare and react appropriately		
	dstpkgchecksum = dstpkginfo.get('checksum')
	dstpkgname = dstpkginfo.get('name')
	dstpkgversion = dstpkginfo.get('version')

	
	
	# if the checksum doesn't match, store it in a list. I guess we can provide more information here as well. Maybe an array as each item of the list.
	if dstpkgchecksum != srcpkgchecksum:
		invalidpkglist.append(dstpkgname + "-" + dstpkgversion)
		match = False
	else:
		match = True

	# verbose information if needed 
	if cfg.verbosity == True:
		if match == False:
			print "Validating checksum of src:{0}-{1} vs dst:{2}-{3}. INVALID".format(srcpkgname, srcpkgversion, dstpkgname, dstpkgversion)
		else: 
			print "Validating checksum of src:{0}-{1} vs dst:{2}-{3}. VALID".format(srcpkgname, srcpkgversion, dstpkgname, dstpkgversion)

# if the list has any items print that and exit
if len(invalidpkglist) > 0:
	print "List of packages that do not match the source server:{0}, channel:{1}".format(cfg.srchost, cfg.srcchannel)
	for package in invalidpkglist:
		print package
else:
	print "All package checksums match"

# logout out of src and dst hosts
srcclient.auth.logout(srckey)
dstclient.auth.logout(dstkey)

