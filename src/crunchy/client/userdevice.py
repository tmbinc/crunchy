from runtime import FPGA
import array

class USERProject(FPGA):
	def send(self, string):
		#print string.encode("hex")
		buf = array.array("c", string[::-1])
		self.jtag.scanuser(buf, self.chainpos)
		buf = buf[::-1]
		return buf.tostring()

	def size_chain(self):
		# flood the buffer with zeros. Then, send ones.
		buf = array.array("c", "\0" * self.MAX_CHAIN_SIZE + "\xFF"	* self.MAX_CHAIN_SIZE)
		self.jtag.scanuser(buf, self.chainpos)
		
		# drop the output while flooding the buffer.
		buf = buf[self.MAX_CHAIN_SIZE:]
		
		# look for the returned FF
		length = buf.index("\xFF")
		assert 0 < length < self.MAX_CHAIN_SIZE
		
		return length - 1

class USERDevice:
	def __init__(self):
		self.commands = []

	def idle(self):
		return self.commands == []

	def assemble(self):
		if self.commands == []:
			self.handler = self.poll
			return self.size() * "\xFF"
		else:
			data, handler = self.commands.pop(0)
			self.handler = handler
			return data

	def receive(self, data):
		if self.handler:
			self.handler(data[:self.size()])
		return data[self.size():]

	def poll(self, data):
		pass
