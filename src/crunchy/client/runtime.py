import array

class FPGA:
	MAX_CHAIN_SIZE = 4096
	def __init__(self, jtag, chainpos):
		self.jtag = jtag
		self.chainpos = chainpos

	def program(self, filename):
		print "programming chainpos %d with %s" % (self.chainpos, filename)
		self.jtag.program(open(filename, "rb"), self.chainpos)
