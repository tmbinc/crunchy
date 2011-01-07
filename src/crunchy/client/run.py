import time

def run_loop(projects, workunit_provider):
	while True: # not workunit_provider.finished():
		for project in projects:
			print project.userproject.chainpos, 
			
			while True:
				result = project.get_workunit()
				if result:
					print "project %d finished workunit: %r" % (project.userproject.chainpos, result)
					workunit_provider.put_workunit(result)
				else:
					break
			while project.need_workunit():
				workunit = workunit_provider.get_workunit()
				print "project %d assigned new workunit: %r" % (project.userproject.chainpos, workunit)
				project.put_workunit(workunit)
			try:
				while not project.idle():
					project.poll()
				project.poll()
			except AssertionError, e:
				print "continue even though", e
		time.sleep(.5)
