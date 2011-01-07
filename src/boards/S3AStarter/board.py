from crunchy.fpga.build import *

class S3AStarter(Board):
	TARGET = "xc3s700afg484"
	PROJECT = "Project_Reset_Clock_XilinxUSER_LED4"
	FILES  = [ProjectFile(ProjectFile.VHDL, "top.vhd")]
	FILES += [ProjectFile(ProjectFile.UCF, "main.ucf")]
