import argparse, struct
from crunchy.core.dbproject import DatabaseProject
from crunchy.core.projectconfig import parse_project_config

def cli_results(args, project):
	from Crypto.Cipher import DES
	for wu in project.workunit_provider.results():
		if wu.results:
			for k in wu.results:
				res = DES.new(struct.pack(">Q", k)).encrypt("\0" * 8)
				if res[:5] != "\0" * 5:
					print "%10d %016x" % (wu.id, k)

def cli_adduser(args, project):
	username = args.username
	password = args.password

	if not project.userbase.adduser(username, password):
		print "failed"

def cli_listuser(args, project):
	for id, username in project.userbase.listusers():
		print "%5d %s" % (id, username)

def cli_expire(args, project):
	project.workunit_provider.expire_pending(args.seconds)

def cli_pending(args, project):
	users = {}
	for id, username in project.userbase.listusers():
		users[id] = username
	
	for workunit, client, date in project.workunit_provider.pending():
		print "%10d %s %s" % (workunit.id, date, users.get(client, "%d" % client))

def cli_progress(args, project):
	nworkunits, nworkunits_pending, nworkunits_finished = project.workunit_provider.progress()
	ntotal = nworkunits + nworkunits_pending + nworkunits_finished
	print "%d+%d+%d / %d (%2.2f %%)" % (nworkunits, nworkunits_pending, nworkunits_finished, ntotal, nworkunits_finished * 100.0 / ntotal)

def cli_status(args, project):
	print "PROGRESS:"
	cli_progress(args, project)
	print "PENDING:"
	cli_pending(args, project)
	print "RESULTS:"
	cli_results(args, project)

def cli_init(args, project):
	project.initialize(args.type, parse_project_config(args.config))

def cli_add_pattern(args, project):
	project.meta.set_pattern(args.index, args.pattern.decode('hex'))

parser = argparse.ArgumentParser(description = "command line tool for crunchy")
parser.add_argument('project', help = "project to operate on")
subparsers = parser.add_subparsers(help='sub-command help')

parser_results = subparsers.add_parser('results', help='show results')
parser_results.set_defaults(func = cli_results)

parser_adduser = subparsers.add_parser('adduser', help='add user')
parser_adduser.add_argument('username', help = "username to add")
parser_adduser.add_argument('password', help = "password")
parser_adduser.set_defaults(func = cli_adduser)

parser_listuser = subparsers.add_parser('users', help='list users')
parser_listuser.set_defaults(func = cli_listuser)

parser_status = subparsers.add_parser('status', help='get project status')
parser_status.set_defaults(func = cli_status)

parser_pending = subparsers.add_parser('pending', help='get project pending')
parser_pending.set_defaults(func = cli_pending)

parser_expire = subparsers.add_parser('expire', help='expire pending workunit')
parser_expire.set_defaults(func = cli_expire)
parser_expire.add_argument('--seconds', default = 3600, type=int)

parser_init = subparsers.add_parser('init', help='initialize database')
parser_init.set_defaults(func = cli_init)
parser_init.add_argument('type', help = "project to use")
parser_init.add_argument('config', help = "project config (excluding board-specific settings")

#haxx haxx haxx
parser_add_pattern = subparsers.add_parser('add_pattern', help='adds a pattern')
parser_add_pattern.set_defaults(func = cli_add_pattern)
parser_add_pattern.add_argument('index', help = "index", type=int)
parser_add_pattern.add_argument('pattern', help = "pattern to add (8 byte hexstring)")

args = parser.parse_args()
project = DatabaseProject(args.project)
args.func(args, project)
