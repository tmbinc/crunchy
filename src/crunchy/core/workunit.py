import struct

class Workunit:
	def __init__(self, id, results = None):
		self.id = id
		
		if results:
			r = results.decode('hex')
			self.results = struct.unpack(">%dQ" % (len(r)/8), r)
		else:
			self.results = None

	def reset(self):
		self.results = None

	def results_as_blob(self):
		if not self.results:
			return ""
		return struct.pack(">%dQ" % len(self.results), *self.results).encode('hex')

	def __repr__(self):
		return "<workunit(%d)=%r>" % (self.id, self.results)
