from crunchy.fpga.build import *

class XUPV2P(Board):
	TARGET = "xc2vp30ff896-6"
	PROJECT = "Project_Reset_Clock_XilinxUSER_LED4"
	FILES  = [ProjectFile(ProjectFile.VHDL, "top.vhd")]
	FILES += [ProjectFile(ProjectFile.UCF, "main.ucf")]
