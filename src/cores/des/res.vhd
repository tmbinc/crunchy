library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use IEEE.numeric_std.all;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity res is
	generic ( nr_results : integer;
				 nr_patterns: integer;
				 workunit_bits: integer); 
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
           COUNTER: out STD_LOGIC_VECTOR(WORKUNIT_BITS - 1 downto 0);
           CLK : in  STD_LOGIC
			  );
end res;

architecture Behavioral of res is

constant scan_size : integer := 16 + nr_patterns * 64;

signal scan_state, scan, scan_set: std_logic_vector(scan_size - 1 downto 0);

signal pattern: std_logic_vector(nr_patterns * 64 - 1 downto 0);
signal result_pipe: std_logic_vector(nr_patterns * nr_results * 64 - 1 downto 0);
signal result_hit, result_hit_r: std_logic_vector(nr_patterns * nr_results - 1 downto 0);
signal result_hit_by_pattern, result_hit_by_pattern_r: std_logic_vector(nr_patterns - 1 downto 0);
signal last_hit: std_logic_vector(63 downto 0);

signal cmd_update, cmd_ack: std_logic;
signal cmd_set: std_logic_vector(7 downto 0);
signal scan_get: std_logic;

-- one more bit
signal cycle_stop, cycle: std_logic_vector(WORKUNIT_BITS downto 0);
signal cycle_full: std_logic_vector(63 downto 0);
signal istatus: std_logic_vector(7 downto 0);

signal request_halt: std_logic;
signal request_halt_reason: std_logic_vector(6 downto 0);

begin
	cmd_set <= scan_set(scan_size - 8 - 1 downto scan_size - 16); -- cmd/status

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

			if scan_get = '1' and cmd_set = x"40" then -- set new pattern, clear cycle, clear last_hit, stop
				pattern <= scan_set(nr_patterns * 64 - 1 downto 0);
				request_halt <= '1';
				request_halt_reason <= "0000000";
				cycle <= (others => '0');
				cycle_stop <= (others => '0');
				last_hit <= (others => '0');
			elsif scan_get = '1' and cmd_set = x"41" then -- resume at cycle (LSB of patterns)
				cycle <= scan_set(WORKUNIT_BITS downto 0);
				cycle_stop <= scan_set(64+WORKUNIT_BITS downto 64);
				request_halt <= '0';
				request_halt_reason <= "0000001";
				last_hit <= (others => '0');
			elsif request_halt = '0' then
				if cycle = cycle_stop then
					request_halt <= '1';
					request_halt_reason <= "0000010";
				end if;

				cycle <= cycle + '1';

				for j in 0 to nr_patterns - 1 loop
					if result_hit_by_pattern_r(j) = '1' then
						last_hit(j) <= '1';
						request_halt <= '1';
						request_halt_reason <= "1" & conv_std_logic_vector(j, 6);
					end if;
				end loop;
			end if;
			
			result_hit_r <= result_hit;
			result_hit_by_pattern_r <= result_hit_by_pattern;
			
			result_pipe <= RESULT & result_pipe(nr_patterns * nr_results * 64 - 1 downto nr_results * 64);
		end if;
	end process;
	
	process (result_pipe, pattern, result_hit_r)
	begin
		for i in 0 to nr_patterns - 1 loop
			for j in 0 to nr_results - 1 loop
				if result_pipe(((nr_results * i) + j) * 64 + 63 downto ((nr_results * i) + j) * 64 ) = pattern(i * 64 + 63 downto i * 64) then
					result_hit(i * nr_results + j) <= '1';
				else
					result_hit(i * nr_results + j) <= '0';
				end if;
			end loop;
			
			if result_hit_r((i + 1) * nr_results - 1 downto i* nr_results) /= (result_hit_r'range => '0') then
				result_hit_by_pattern(i) <= '1';
			else
				result_hit_by_pattern(i) <= '0';
			end if;
		end loop;
	end process;

	-- scan out: 8 bit ID, 8 bit status, 64 bit cycle, 64 bit last hit
	scan_state(scan_size - 1 downto scan_size - 16 - 64 - 64) <= x"10" & istatus & cycle_full & last_hit;
	scan_state(scan_size - 16 - 64 - 64 - 1 downto 0) <= (others => '0');

	SCAN_TDO <= scan(0);
	
	cycle_full(63 downto WORKUNIT_BITS+1) <= (others => '0');
	cycle_full(WORKUNIT_BITS downto 0) <= cycle;
	
	counter <= cycle;
	
	istatus <= request_halt_reason & request_halt;
	
		-- scanning
	process (scan_drck)
	begin
		if rising_edge(scan_drck) then
			if scan_shift = '1' then
				scan <= SCAN_TDI & scan(16 + nr_patterns * 64 - 1 downto 1);
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

