from crunchy.fpga.build import *

class DM8000(Board):
	TARGET = "xc3s500efg320"
	PROJECT = "Project_Reset_Clock_XilinxUSER_LED4"
	FILES  = [ProjectFile(ProjectFile.VHDL, "top.vhd")]
	FILES += [ProjectFile(ProjectFile.UCF, "main.ucf")]
