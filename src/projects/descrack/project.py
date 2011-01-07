from crunchy.fpga.build import Project, ProjectFile

class descrack(Project):
	CORES = ["des"]
	FILES = [ProjectFile(ProjectFile.VHDL, "descrack.vhd")]
	TOP_MODULE = "descrack_Reset_Clock_XilinxUSER_LED4"
	PARAMETERS = {"NR_CORES": 1, "NR_PATTERNS" : 16, "WORKUNIT_BITS": 40}
