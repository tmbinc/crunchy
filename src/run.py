import jtag, array, struct, sys, time
from crunchy.client.userdevice import USERProject
from crunchy.client.descrack import DESCrack
from crunchy.core.workunit import Workunit
from crunchy.client.workunit_remote import RemoteWorkunitProvider

import argparse

def setup_jtag(args):
	jt = jtag.JTAG()
	chain = jt.connect(args.cable, product=int(args.productid, 0x10))

	print "DETECTED CHAIN CONFIGURATION:"

	print "TDI ->",
	print ' -> '.join("%08x" % x for x in chain),
	print "-> TDO"
	
	return jt, chain


# HAXX HAXX (they need to go into boards/...)
class Dance2048:
	NR_CORES = 6
	ID = 0x1129e093
	NR_DEVICES = 9

class S3AStarter:
	NR_CORES = 1
	NR_DEVICES = 1
	ID = 0x02228093

def CreateProject(chainpos, jtag, id, platform, project_config, program, meta):
	assert id == platform.ID, "FPGA ID incorrect"

	fpga = USERProject(jtag, chainpos)

	if program:
		fpga.program(program)

	# TODO: get different project configuration depending on platform/board
	NR_CORES = platform.NR_CORES
	WORKUNIT_BITS = 38

	project = DESCrack(fpga, project_config, meta)

	assert fpga.size_chain() == project.size()

	return project

### global config (for all fpgas)
import Crypto.Cipher.DES

def k7to8(key):
	res = ""
	for i in range(8):
		k = (key >> ((7-i) * 7)) & 0x7F
		k <<= 1
		res += chr(k)
	return res

def gen_test(key):
	key = k7to8(key)
	print "key", key.encode("hex")
	res = Crypto.Cipher.DES.new(key).encrypt("\x00" * 8)
	print "res", res.encode("hex")
	return res

bitstream = None

def setup_provider(projectid, url, user, password):
	return RemoteWorkunitProvider(projectid, url, user, password)

parser = argparse.ArgumentParser(description = "command line tool for crunchy runtime")
parser.add_argument('project', help = "project to operate on")
parser.add_argument('projectconfig', help = "project configuration")
parser.add_argument('platform', help = "platform")
parser.add_argument('url', help = "url of project workunit server")
parser.add_argument('username', help = "username")
parser.add_argument('password', help = "password", default = "pass0")
parser.add_argument('--instances', help = "nr of instances", type=int, default = 1)
parser.add_argument('--bitstream', help = "bitstream to program", default = None)
parser.add_argument('--cable', help = "jtag cable", default = "ftdi")
parser.add_argument('--productid', help = "jtag cable product id (for ftdi)", default = "6110")

from crunchy.core.projectconfig import parse_project_config

args = parser.parse_args()

workunit_provider = setup_provider(args.project, args.url, args.username, args.password)

project_config = parse_project_config(args.projectconfig)

project_meta = workunit_provider.get_meta()

jtag, chain = setup_jtag(args)

# HAXX HAXX (uh oh, this is really bad.)
platform = eval(args.platform)()

projects = [CreateProject(i, jtag, chain[i], platform, project_config, args.bitstream, project_meta) for i in range(args.instances)]

from crunchy.client.run import run_loop

run_loop(projects, workunit_provider)

print "finished"
