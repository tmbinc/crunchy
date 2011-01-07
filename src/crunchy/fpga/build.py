class Dependency:
	CORES = []

class Board(Dependency):
	TOP_MODULE = "top"

class Core(Dependency):
	pass

class Project(Dependency):
	pass

import tempfile, os, subprocess, os

class Action:
	pass

class ToolFailureException:
	def __init__(self, tool, errorcode):
		self.tool = tool
		self.errorcode = errorcode
	
	def __repr__(self):
		return "Tool %s executed with error %d" % (self.tool.TOOL[0], self.errorcode)

class XilinxToolWithResonsefile(Action):
	def __init__(self, previous = None):
		self.prefix = []
		self.suffix = []
		self.cwd = os.path.abspath("out_" + self.TOOL[0])
		self.previous = previous
		try:
			os.mkdir(self.cwd)
		except:
			pass

	def write_options(self):
		file = tempfile.NamedTemporaryFile(delete = False)
		file.write(''.join([x + "\n" for x in (self.prefix + ["-%s %s" % x for x in self.opt.items()] + self.suffix)]))
		print (''.join([x + "\n" for x in (self.prefix + ["-%s %s" % x for x in self.opt.items()] + self.suffix)]))
		file.flush()
		return file.name

	def from_previous(self, input_filename):
		return os.path.join(self.previous.cwd, input_filename)
	
	def from_source(self, source_filename):
		return os.path.abspath(source_filename)

	def into_cwd(self, output_filename):
		return os.path.join(self.cwd, output_filename)

	def run(self):
		responsefile = self.write_options()
		print "running '%s' in %s" % (self.TOOL[0], self.cwd)
		result = subprocess.call(self.TOOL + [ responsefile ], cwd = self.cwd)
		os.remove(responsefile)
		
		if result:
			raise ToolFailureException(self, result)

class XST(XilinxToolWithResonsefile):
	TOOL = ["xst" , "-ifn"]

	def __init__(self, top, synth_target, opt_mode, opt_level, projectfile, ofn):
		XilinxToolWithResonsefile.__init__(self)
		
		self.prefix = ["run"]
		
		self.opt = {
			"ifn": projectfile,
			"ifmt": "mixed",
			"top": top,
			"ofn": ofn,
			"ofmt": "NGC",
			"p": synth_target,
			"opt_mode": opt_mode,
			"opt_level": opt_level,
		}

		self.files = []
		
	def add_file(self, type, name):
		self.files += [(type, name)]

	def create_project_file(self):
		prj = open(self.into_cwd(self.opt["ifn"]), "w")
		for i in self.files:
			prj.write("%s work %s\n" % (i[0], self.from_source(i[1])))
		prj.close()

	def run(self):
		self.create_project_file()
		XilinxToolWithResonsefile.run(self)

class NGDBuild(XilinxToolWithResonsefile):
	TOOL = ["ngdbuild", "-f"]
	def __init__(self, previous, synth_target, ucf, ifn, ofn):
		XilinxToolWithResonsefile.__init__(self, previous)
		
		self.opt = {
			"intstyle": "ise",
			"dd": self.cwd,
			"nt": "timestamp",
			"uc": self.from_source(ucf),
			"p": synth_target,
		}
		
		self.suffix = [self.from_previous(ifn), self.into_cwd(ofn)]

class Map(XilinxToolWithResonsefile):
	TOOL = ["map", "-f"]
	
	def __init__(self, previous, synth_target, ofn, ifn):
		XilinxToolWithResonsefile.__init__(self, previous)

		self.opt = {
			"intstyle": "ise",
			"p": synth_target,
			"cm": "area",
			"pr": "b",
			"k": "4",
			"c": "100",
			"tx": "off",
			"o": self.into_cwd(ofn)}

		self.suffix = [self.from_previous(ifn)]

class PAR(XilinxToolWithResonsefile):
	TOOL = ["par", "-f"]
	def __init__(self, previous, ifn, ofn):
		XilinxToolWithResonsefile.__init__(self, previous)
		
		self.opt = {
			"w": "",
			"intstyle": "ise",
			"ol": "std",
			"t": 1
		}
		
		self.suffix = [self.from_previous(ifn), self.into_cwd(ofn)]

class Bitgen(XilinxToolWithResonsefile):
	TOOL = ["bitgen", "-w", "-f"]
	def __init__(self, previous, ifn, ofn):
		XilinxToolWithResonsefile.__init__(self, previous)
		
		self.opt = {}
		
		self.suffix = [self.from_previous(ifn), self.into_cwd(ofn)]

class XilinxProject:
	def __init__(self):
		self.ucf = None
		self.xst_files = []
		self.options = {}
		self.parameters = {}
	
	def set_synth_target(self, target):
		self.options["synth_target"] = target
	
	def set_top(self, top):
		self.options["top"] = top

	def prepare(self):
		self.synth_target = self.options["synth_target"]
		self.xst = XST(top=self.options["top"], synth_target = self.synth_target, opt_mode="Speed", opt_level="1", projectfile="test.prj", ofn = "out.ngc")
		for i in self.xst_files:
			self.xst.add_file(*i)
		
		self.ngdbuild = NGDBuild(previous = self.xst, synth_target = self.synth_target, ucf = self.ucf, ifn = "out.ngc", ofn = "out.ngd")
		self.map = Map(previous = self.ngdbuild, synth_target = self.synth_target, ofn = "map_out.ncd", ifn = "out.ngd")
		self.par = PAR(previous = self.map, ifn = "map_out.ncd", ofn = "par_out.ncd")
		self.bitgen = Bitgen(previous = self.par, ifn = "par_out.ncd", ofn = "out.bit")

		self.actions = [self.xst, self.ngdbuild, self.map, self.par, self.bitgen]
	
	def add(self, projectfile):
		if projectfile.type in [ProjectFile.VERILOG, ProjectFile.VHDL]:
			self.xst_files.append(({ProjectFile.VERILOG: "verilog", ProjectFile.VHDL: "VHDL"}[projectfile.type], projectfile.filename))
		elif projectfile.type == ProjectFile.UCF:
			assert self.ucf == None
			self.ucf = projectfile.filename
	
	def run(self):
		self.prepare()
		for action in self.actions:
			try:
				print "executing %s" % action
				action.run()
			except ToolFailureException, e:
				print "build failed:", e
				raise e

class ProjectFile:
	VERILOG, VHDL, UCF = range(3)
	
	def __init__(self, type, filename):
		self.type = type
		self.filename = filename

