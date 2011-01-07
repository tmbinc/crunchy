import argparse, struct

from crunchy.core.dbworkunitprovider import DatabaseWorkunitProvider

from crunchy.core.dbproject import DatabaseProject

from crunchy.server.frontend import run_server

parser = argparse.ArgumentParser(description = "crunchy server")
parser.add_argument('project', help = "project to operate on")
args = parser.parse_args()

project = DatabaseProject(args.project)
run_server(project)
