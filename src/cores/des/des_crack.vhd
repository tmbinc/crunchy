library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

entity des_crack is
		Generic (
					WORKUNIT_BITS : integer
				);
		Port ( SCAN_CAPTURE : in	STD_LOGIC;
					 SCAN_DRCK : in	STD_LOGIC;
					 SCAN_RESET : in	STD_LOGIC;
					 SCAN_SEL : in	STD_LOGIC;
					 SCAN_SHIFT : in	STD_LOGIC;
					 SCAN_TDI : in	STD_LOGIC;
					 SCAN_UPDATE : in	STD_LOGIC;
					 SCAN_TDO : out	STD_LOGIC;
					 KEY_COUNTER : in STD_LOGIC_VECTOR(WORKUNIT_BITS-1 downto 0);
					 RESULT: out STD_LOGIC_VECTOR(63 downto 0);
					 CLK : in	STD_LOGIC
				);
end des_crack;

architecture Behavioral of des_crack is

signal scan_state, scan, scan_set: std_logic_vector(63 downto 0);

signal des_in, des_out: std_logic_vector(63 downto 0);

signal des_key: std_logic_vector(55 downto 0);

signal cmd: std_logic_vector(3 downto 0);
signal cmd_update, cmd_ack, scan_get: std_logic;

COMPONENT des
PORT(
	desIn : IN std_logic_vector(63 downto 0);
	key : IN std_logic_vector(55 downto 0);
	decrypt : IN std_logic;
	clk : IN std_logic;
	desOut : OUT std_logic_vector(63 downto 0)
	);
END COMPONENT;

begin
	Inst_des: des PORT MAP(
		desOut => des_out,
		desIn => des_in,
		key => des_key,
		decrypt => '0',
		clk => clk
	);
	
	cmd <= scan_set(59 downto 56);

	process (clk)
	begin
		if rising_edge(clk) then
			if cmd_update = '1' and cmd_ack = '0' then
				cmd_ack <= '1';
				scan_get <= '1';
			elsif cmd_update = '0' then
				cmd_ack <= '0';
				scan_get <= '0';
			else
				scan_get <= '0';
			end if;
			
			if scan_get = '1' and cmd = x"5" then -- cmd 5: set key prefix
				des_key(55 downto WORKUNIT_BITS) <= scan_set(55 downto WORKUNIT_BITS);
			end if;
		end if;
	end process;

	RESULT <= des_out;
	
	des_key(WORKUNIT_BITS - 1 downto 0) <= KEY_COUNTER;

	des_in <= (others => '0'); -- encrypting zeros

	scan_state <= x"d" & "0000" & des_key;

	SCAN_TDO <= scan(0);
	
		-- scanning
	process (scan_drck)
	begin
		if rising_edge(scan_drck) then
			if scan_shift = '1' then
				scan <= SCAN_TDI & scan(63 downto 1);
			elsif scan_capture = '1' then
				scan <= scan_state;
			end if;
		end if;
	end process;

		-- cmd if
	process (scan_update, cmd_ack, scan_sel, cmd_update, scan)
	begin
		if scan_update = '1' and scan_sel = '1' and cmd_update = '0' then
			scan_set <= scan;
			cmd_update <= '1';
		elsif cmd_ack = '1' then
			cmd_update <= '0';
		end if;
	end process;

end Behavioral;

