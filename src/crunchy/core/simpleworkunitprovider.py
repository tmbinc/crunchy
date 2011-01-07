import os
import cPickle as pickle
import array

class SimpleWorkunitProvider:
	def __init__(self):
		self.workunits = array.array("c", "\1" * (1<<18))
		self.workunits_pending = []
		self.workunits_finished = []
		self.workunits_finished_interesting = []
		try:
			self.load()
		except IOError:
			pass

	def get_workunit(self):
		i = self.workunits.index("\1")
		if i == -1:
			return None
		self.workunits[i] = "\0"
		workunit = Workunit(i)
		self.workunits_pending.append(workunit)
		return workunit

	def put_workunit(self, workunit):
		print "finished workunit %d" % workunit.prefix
		if workunit.results:
			self.workunits_finished_interesting.append(workunit)
		self.workunits_pending.remove(workunit)
		self.workunits_finished.append(workunit.prefix)
		self.sync()

	def load(self):
		self.workunits = array.array("c", open("state-bitmap", "rb").read())
		self.workunits_pending, self.workunits_finished, self.workunits_finished_interesting = pickle.load(open("state", "rb"))
		
		for i in self.workunits_pending:
			self.workunits[i.prefix] = "\1"
			i.reset()

		self.workunits_pending = []

	def sync(self):
		self.workunits_finished = []
		pickle.dump((self.workunits_pending, self.workunits_finished, self.workunits_finished_interesting), open("state-new", "wb"))
		open("state-new-bitmap", "wb").write(self.workunits.tostring())

		try:
			os.remove("state")
			os.remove("state-bitmap")
		except OSError:
			pass

		os.rename("state-new", "state")
		os.rename("state-new-bitmap", "state-bitmap")

	def get_progress(self):
		return len(self.workunits), self.workunits.index("\1")

	def finished(self):
		return not self.workunits_pending and not self.workunits
