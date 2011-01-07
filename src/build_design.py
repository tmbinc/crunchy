from crunchy.fpga.build import Board, Core, ProjectFile, XilinxProject
from crunchy.core.projectconfig import parse_project_config
import os, sys
from crunchy.fpga.wrap import build_wrapper

def import_by_name(name):
	mod = __import__(name)
	components = name.split('.')
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod

def LoadBoard(board):
	module = import_by_name("boards.%s.board" % board)
	obj = getattr(module, board)()
	obj.ROOT = "boards/%s" % board
	return obj

def LoadProject(project):
	module = import_by_name("projects.%s.project" % project)
	obj = getattr(module, project)()
	obj.ROOT = "projects/%s" % project
	return obj

def LoadCore(core):
	module = import_by_name("cores.%s.core" % core)
	obj = getattr(module, core)()
	obj.ROOT = "cores/%s" % core
	return obj

def build_bitstream(board, project, project_config):
	try:
		target_board = LoadBoard(board)
	except ImportError:
		raise Exception("board '%s' not found" % board)
	try:
		target_project = LoadProject(project)
	except ImportError:
		raise Exception("project '%s' not found" % project)
	target_cores = {}
	
	for i in project_config:
		assert i in target_project.PARAMETERS, "project config '%s': unknown property" % i

	# merge in defaults
	project_config = dict(target_project.PARAMETERS, **project_config)

	# load all dependencies
	core_dependencies = target_project.CORES + target_board.CORES

	while len(core_dependencies):
		core = core_dependencies.pop()
		try:
			if core not in target_cores:
				target_cores[core] = LoadCore(core)
		except ImportError:
			raise Exception("dependency '%s' for project '%s' not found" % (core, project))
		core_dependencies += target_cores[core].CORES

	p = XilinxProject()

	p.set_synth_target(target_board.TARGET)
	p.set_top(target_board.TOP_MODULE)

	for d in [target_project, target_board] + target_cores.values():
		for f in d.FILES:
			p.add(ProjectFile(f.type, os.path.join(d.ROOT, f.filename)))

	open("wrap.vhd", "w").write(build_wrapper(target_board.PROJECT, [(target_project.TOP_MODULE, project_config)]))
	p.add(ProjectFile(ProjectFile.VHDL, "wrap.vhd"))
	
	p.run()

build_bitstream(sys.argv[1], sys.argv[2], parse_project_config(sys.argv[3]))
