from userdevice import USERDevice
import struct, time

class DES(USERDevice):
	def __init__(self, index, workunit_bits):
		USERDevice.__init__(self)
		self.index = index
		self.workunit_bits = workunit_bits
	
	def set_prefix(self, prefix):
		prefix += "\x00" * 7
		prefix = prefix[:7]
		# command 5 is "set prefix"
		self.commands.append((chr(5) + prefix, self.poll))

	def set_workunit(self, workunit):
		self.workunit = workunit
		if self.workunit:
			self.prefix = workunit.id << (self.workunit_bits)
		else:
			self.prefix = 0 # dummy
		self.set_prefix(struct.pack(">Q", self.prefix)[1:])

	def size(self):
		return 1 + 7

	def poll(self, data):
		#print "DES %d received"  % self.index, data.encode("hex"), 
		pass

	def k7to8(self, key):
		res = ""
		for i in range(8):
			k = (key >> ((7-i) * 7)) & 0x7F
			k <<= 1
			res += chr(k)
		return res

	def verify(self, cycle):
		from Crypto.Cipher import DES
		key = self.k7to8(self.prefix | cycle)
		res = DES.new(key, DES.MODE_ECB).encrypt("\0" * 8)
		
#		print key.encode("hex")," -> ", res.encode("hex")

		return key,res

class RES(USERDevice):
	CMD_RESET = "\x40"
	CMD_RESUME_AT = "\x41"
	
	EVENT_FOUND, EVENT_WORKUNIT_DONE = range(2)

	def __init__(self, nr_patterns, event, start = 0, stop = 0):
		USERDevice.__init__(self)
		self.nr_patterns = nr_patterns
		self.event = event
		self.start = start
		self.stop = stop

	def size(self):
		return 2 + self.nr_patterns * 8
	
	def set_patterns(self, patterns):
		patterns =''.join(patterns)
		assert len(patterns) == self.nr_patterns * 8
		cmd = "\xFF" + self.CMD_RESET + patterns
		self.commands.append((cmd, None))
	
	def restart(self, start, stop):
		self.start = start
		self.stop = stop
		self.start_time = time.time()
		self.resume()

	def resume(self):
		print "Resuming at %016lx..%016lx" % (self.start, self.stop)
		cmd = "\xFF" + self.CMD_RESUME_AT + (self.size()-2-8-8) * "\xFF" + struct.pack(">QQ", self.stop, self.start)
		self.commands.append((cmd, None))

	def poll(self, data):
		id, status, cycle, hit = struct.unpack(">BBQQ", data[:18])
		assert id == 0x10, "RES ID incorrect"
		found = status & 0x80 and True or False
		halted = status & 1 and True or False
		
		nr_cycles = cycle - self.start
		
		timediff = time.time() - self.start_time
		if timediff > 5:
			rate = "%.3f MHz" % (cycle / timediff / 1000000)
		else:
			rate = ""
		
		perc = cycle * 100 / self.stop
		print "RES not_running=%d, found=%r, reason=%02x, cycle=%016x, hit=%016x (%d %%) %s" % (status & 1, found, (status>>1) & 0x3F, cycle, hit, perc, rate)
		
		base = None

		if found:
			for i in range(self.nr_patterns):
				if hit & 1 << (self.nr_patterns - 1 - i):
					base = cycle - 20 - i - 1
					print "pattern %d @ %016x" % (i, base)

			assert base is not None, "no hit but stopped"
			
			self.start = base + 1
			self.resume()

		if halted and not found:
			print "DONE."
		
		self.event(halted, (cycle, self.stop), base)

class DESCrack:
	PARAMETERS = {"NR_CORES": 1, "NR_PATTERNS" : 16, "WORKUNIT_BITS": 32}
	
	MAX_LATENCY = 40
	
	def size(self):
		return sum([x.size() for x in self.cores])

	def __init__(self, userproject, parameters, project_meta):
		self.parameters = self.PARAMETERS
		self.parameters.update(parameters)
		self.userproject = userproject
		
		meta_workunit_bits, str_patterns = project_meta.split(",")
		meta_workunit_bits = int(meta_workunit_bits)
		assert meta_workunit_bits == self.parameters["WORKUNIT_BITS"], "workunit bits disagrees between server and local config"
		
		patterns = []
		while len(str_patterns):
			pattern = str_patterns[:16].decode('hex')
			assert len(pattern) == 8
			patterns.append(pattern)
			
			str_patterns = str_patterns[16:]
			
		self.patterns = patterns
		
		self.nr_cores = self.parameters["NR_CORES"]
		
		self.waiting = True
		self.workunits = []
		self.workunits_finished = []
		
		assert len(patterns) <= self.parameters["NR_PATTERNS"]
		
		# fill with dummy entries
		patterns += ["\0" * 8] * (self.parameters["NR_PATTERNS"] - len(patterns))
		
		self.cores = []
		for i in range(self.nr_cores):
			c = DES(i, self.parameters["WORKUNIT_BITS"])
			self.cores.append(c)
			
		self.des = self.cores[:]
		self.res = RES(self.parameters["NR_PATTERNS"], self.res_event)
		self.cores.append(self.res)
		
	# micromanagement
	def idle(self):
		return reduce(lambda x, y: x and y, [core.idle() for core in self.cores])

	def poll(self):
		string_to_send = ''.join(core.assemble() for core in self.cores)
		
		response = self.userproject.send(string_to_send)
		
		for core in self.cores:
			response = core.receive(response)
		
		assert response == "", "%d bytes left in response" % len(response)

	# macromanagement
	def need_workunit(self):
		return self.waiting

	def put_workunit(self, workunit):
		assert self.waiting
		self.workunits.append(workunit)
		
		if len(self.workunits) == self.nr_cores:
			self.waiting = False
			for des in self.des:
				des.set_workunit(self.workunits.pop(0))

			# reset pattern matcher
			self.res.set_patterns(self.patterns)
			
			# resume cracking
			self.res.restart(0, (1<<(self.parameters["WORKUNIT_BITS"])) + self.MAX_LATENCY)
			self.res.resume()

	def get_workunit(self):
		if self.workunits_finished:
			return self.workunits_finished.pop(0)
		return None

	def res_event(self, halted, progress, hit):
		if self.waiting:
			return

		if halted and hit is None:
			self.workunits = [d.workunit for d in self.des]
			print "DONE, returning workunits", self.workunits
			
			# reset matcher
			self.res.set_patterns(self.patterns)
			self.workunits_finished += [x for x in self.workunits if x is not None]
			self.workunits = []
			self.waiting = True

		if hit is not None:
			found = False
			for des in self.des:
				if des.workunit is None:
					continue
				key, res = des.verify(hit)
				
				res = res[:5] + "\0\0\0"
				if res in self.patterns:
					if des.workunit.results is None:
						des.workunit.results = []
					des.workunit.results.append(struct.unpack(">Q", key)[0])
					print "VERIFY OK: key=%s" % key.encode("hex")
					found = True
			assert found, "manual verify failed for hit %08x" % (hit)
