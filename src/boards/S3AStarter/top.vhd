library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

library unisim;
use unisim.vcomponents.all;

entity top is
		Port ( leds : out	STD_LOGIC_vector(3 downto 0);
					 clk_50mhz : in STD_LOGIC
				);
end top;

architecture Behavioral of top is

signal clk: std_logic;
signal led: std_logic_vector(3 downto 0);

component Project_Reset_Clock_XilinxUSER_LED4 is
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
end component;

signal SCAN_CAPTURE : std_logic;
signal SCAN_DRCK : std_logic;
signal SCAN_RESET : std_logic;
signal SCAN_SEL : std_logic;
signal SCAN_SHIFT : std_logic;
signal SCAN_TDI : std_logic;
signal SCAN_UPDATE : std_logic;
signal SCAN_TDO : std_logic;

signal RESET : std_logic;

begin

	-- Clock
	clk <= clk_50mhz;

	-- Display LEDs
	leds <= led;

	-- JTAG primitive
	BSCAN_VIRTEX2_inst : BSCAN_VIRTEX2
	port map (
		CAPTURE => SCAN_CAPTURE,
		DRCK1 => SCAN_DRCK,
		DRCK2 => open,
		RESET => SCAN_RESET,
		SEL1 => SCAN_SEL,
		SEL2 => open,
		SHIFT => SCAN_SHIFT,
		TDI => SCAN_TDI,
		UPDATE => SCAN_UPDATE,
		TDO1 => SCAN_TDO,
		TDO2 => '0'
	);

	-- Main project
	Project_Reset_Clock_XilinxUSER_LED4_inst : Project_Reset_Clock_XilinxUSER_LED4
	port map (
		RESET => reset,

		CLK => clk,

		SCAN_CAPTURE => SCAN_CAPTURE,
		SCAN_DRCK => SCAN_DRCK,
		SCAN_RESET => SCAN_RESET,
		SCAN_SEL => SCAN_SEL,
		SCAN_SHIFT => SCAN_SHIFT,
		SCAN_TDI => SCAN_TDI,
		SCAN_UPDATE => SCAN_UPDATE, 
		SCAN_TDO => SCAN_TDO,
		
		LED => led
	);
	
	-- fake reset
	RESET <= '0';

end Behavioral;
