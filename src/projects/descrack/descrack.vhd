library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

library unisim;
use unisim.vcomponents.all;

entity descrack_Reset_Clock_XilinxUSER_LED4 is

	Generic (
		NR_CORES: integer := 1;
		NR_PATTERNS: integer := 16;
		WORKUNIT_BITS: integer
	);

	Port (
		-- Reset
		RESET        : in std_logic;

		-- Clock
		CLK          : in std_logic;

		-- XilinxUSER
		SCAN_CAPTURE : in std_logic;
		SCAN_DRCK    : in std_logic;
		SCAN_RESET   : in std_logic;
		SCAN_SEL     : in std_logic;
		SCAN_SHIFT   : in std_logic;
		SCAN_TDI     : in std_logic;
		SCAN_UPDATE  : in std_logic;
		SCAN_TDO     : out std_logic;		
		
		-- LED4
		LED          : out std_logic_vector(3 downto 0)
	);
end descrack_Reset_Clock_XilinxUSER_LED4;

architecture Behavioral of descrack_Reset_Clock_XilinxUSER_LED4 is

COMPONENT des_crack
generic ( workunit_bits: integer );
	PORT(
		SCAN_CAPTURE : IN std_logic;
		SCAN_DRCK : IN std_logic;
		SCAN_RESET : IN std_logic;
		SCAN_SEL : IN std_logic;
		SCAN_SHIFT : IN std_logic;
		SCAN_TDI : IN std_logic;
		SCAN_UPDATE : IN std_logic;
		SCAN_TDO : OUT std_logic;
		KEY_COUNTER : in STD_LOGIC_VECTOR(WORKUNIT_BITS-1 downto 0);
		RESULT: out STD_LOGIC_VECTOR(63 downto 0);
		CLK : IN std_logic
	);
END COMPONENT;

COMPONENT res
generic ( nr_results : integer; nr_patterns: integer; workunit_bits: integer );
	Port ( SCAN_CAPTURE : in  STD_LOGIC;
		SCAN_DRCK : in  STD_LOGIC;
		SCAN_RESET : in  STD_LOGIC;
		SCAN_SEL : in  STD_LOGIC;
		SCAN_SHIFT : in  STD_LOGIC;
		SCAN_TDI : in  STD_LOGIC;
		SCAN_UPDATE : in  STD_LOGIC;
		SCAN_TDO : out  STD_LOGIC;
		STATUS: out STD_LOGIC;
		RESULT: in STD_LOGIC_VECTOR(nr_results * 64 - 1 downto 0);
		COUNTER : out STD_LOGIC_VECTOR(workunit_bits - 1 downto 0);
		CLK : in  STD_LOGIC
	);
end component;

signal result_buffer: std_logic_vector(NR_CORES * 64 - 1 downto 0);
signal tdo_chain, tdi_chain: std_logic_vector(NR_CORES downto 0);

signal counter: std_logic_vector(WORKUNIT_BITS - 1 downto 0);

begin
	LED <= counter(27 downto 24);
	
	res_0: res 
		GENERIC MAP (
			NR_RESULTS => NR_CORES,
			NR_PATTERNS => NR_PATTERNS,
			WORKUNIT_BITS => WORKUNIT_BITS
		)

		PORT MAP (
			SCAN_CAPTURE => SCAN_CAPTURE,
			SCAN_DRCK => SCAN_DRCK,
			SCAN_RESET => SCAN_RESET,
			SCAN_SEL => SCAN_SEL,
			SCAN_SHIFT => SCAN_SHIFT,
			SCAN_TDI => tdi_chain(NR_CORES),
			SCAN_UPDATE => SCAN_UPDATE,
			SCAN_TDO => tdo_chain(NR_CORES),
			RESULT => result_buffer,
			COUNTER => counter,
			CLK => clk
		);
	
	des_blocks: for i in 0 to NR_CORES - 1 generate
		des: des_crack 
		GENERIC MAP (
			WORKUNIT_BITS => WORKUNIT_BITS
		)
		PORT MAP(
			SCAN_CAPTURE => SCAN_CAPTURE,
			SCAN_DRCK => SCAN_DRCK,
			SCAN_RESET => SCAN_RESET,
			SCAN_SEL => SCAN_SEL,
			SCAN_SHIFT => SCAN_SHIFT,
			SCAN_TDI => tdi_chain(i),
			SCAN_UPDATE => SCAN_UPDATE,
			SCAN_TDO => tdo_chain(i),
			KEY_COUNTER => counter,
			RESULT => result_buffer((i+1) * 64- 1 downto i * 64),
			CLK => clk
		);
	
	end generate;

	-- chain up all cores
	tdi_chain <= tdo_chain(NR_CORES - 1 downto 0) & SCAN_TDI;
	SCAN_TDO <= tdo_chain(NR_CORES);

end Behavioral;
