from crunchy.fpga.build import Board, ProjectFile

class Dance2048(Board):
	TARGET = "xc2vp50ff1152-6"
	PROJECT = "Project_Reset_Clock_XilinxUSER_LED4"
	FILES  = [ProjectFile(ProjectFile.VHDL, "top.vhd")]
	FILES += [ProjectFile(ProjectFile.UCF, "main.ucf")]
