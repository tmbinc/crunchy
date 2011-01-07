
class ProjectMeta:
	# FIXME: shared with Project
	DEFAULT_CONFIG = {"NR_PATTERNS" : 16, "WORKUNIT_BITS": 40, "KEYSPACE_BITS": 56}

	def __init__(self, project, project_config):
		self.project = project
		
		if project_config:
			for key, value in self.DEFAULT_CONFIG.items():
				if key not in project_config:
					project_config[key] = value
			for key, value in project_config.items():
				self.project.set_meta(key, str(value))
		self.WORKUNIT_BITS = int(self.project.get_meta("WORKUNIT_BITS", -1))
		self.KEYSPACE_BITS = int(self.project.get_meta("KEYSPACE_BITS", -1))
		self.NR_PATTERNS = int(self.project.get_meta("NR_PATTERNS", -1))

	def get_number_of_workunits(self):
		assert self.WORKUNIT_BITS != -1, "uninitialized project"
		return 1<<(self.KEYSPACE_BITS-self.WORKUNIT_BITS)

	def set_pattern(self, index, pattern):
		assert 0 <= index < self.NR_PATTERNS
		assert len(pattern) == 8
		self.project.set_meta("pattern%d" % index, 'p' + pattern.encode('hex'))

	def get_pattern(self, index):
		return self.project.get_meta("pattern%d" % index, 'p' + ("\0" * 8).encode('hex'))[1:]

	def build_meta_string(self):
		res = ""
		for i in range(self.NR_PATTERNS):
			p = self.get_pattern(i)
			res += p
		return ("%d," % self.WORKUNIT_BITS) + res
