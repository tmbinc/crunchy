from crunchy.fpga.build import Core, ProjectFile

class des(Core):
	FILES = [ProjectFile(ProjectFile.VERILOG, x) for x in ["crp.v", "des.v", "key_sel.v", "sbox1.v", "sbox2.v", "sbox3.v", "sbox4.v", "sbox5.v", "sbox6.v", "sbox7.v", "sbox8.v"]]
	FILES += [ProjectFile(ProjectFile.VHDL, x) for x in ["res.vhd", "des_crack.vhd"]]
