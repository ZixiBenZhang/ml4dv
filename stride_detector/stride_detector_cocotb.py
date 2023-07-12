import functools
from pprint import pprint

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, ReadWrite, ReadOnly, Event

NUM_STRIDES = 32
STRIDE_MIN = -16
STRIDE_MAX = 15

NO_STRIDE = 0
SINGLE_STRIDE = 1
DOUBLE_STRIDE = 2

# Gathers the coverage, coverage bins are:
# * stride_1_seen - One bin per possible stride, counts when a single stride has
#   been detected
# * stride_2_seen - One bin per pair of possible strides, counts when a double
#   stride has been detected. Note that the bins where both strides are the same
#   will never be hit (as these are single stride patterns)
# * misc_bins - Various bins grouped in a dictionary
#  - single_stride_[n|p]_overflow - Counts when an incoming stream of values
#    has a valid single stride but that stride is below the minimimum (n) or
#    above the maximum (p) stride
#  - double_stride_[n|p][n|p] - Counts when an incoming stream of values
#    has a valid double stride but those strides ar below the minimimum (n) or
#    above the maximum (p) strides, nn indicates both a below the minimum, where
#    np indicataes one is below the minimum and the other above the maximum.
#  - no_stride_to_[single|double] - No repeating stride pattern has been
#    observed in values for at least 16 values followed by the observation of a
#    single/double stride pattern for at least 16 values
#  - [single|double]_stride_[double|single] - A single/double repeating stride
#    pattern has been observed followed by a double/single pattern

class CoverageMonitor:
    def __init__(self, dut):
        self.stride_1_seen = [0] * NUM_STRIDES
        self.stride_2_seen = []

        for i in range(NUM_STRIDES):
            self.stride_2_seen.append([0] * NUM_STRIDES)

        self.signals = {
                'clk'   : dut.clk_i,
                'valid' : dut.valid_i,
                'value' : dut.value_i,
                'stride_1' : dut.stride_1_o,
                'stride_1_valid' : dut.stride_1_valid_o,
                'stride_2' : dut.stride_2_o,
                'stride_2_valid' : dut.stride_2_valid_o,
        }

        self.misc_bins = {
                'single_stride_n_overflow' : 0,
                'single_stride_p_overflow' : 0,
                'double_stride_nn_overflow' : 0,
                'double_stride_np_overflow' : 0,
                'double_stride_pn_overflow' : 0,
                'double_stride_pp_overflow' : 0,
                'no_stride_to_double' : 0,
                'no_stride_to_single' : 0,
                'single_stride_to_double' : 0,
                'double_stride_to_single' : 0,
        }

        self.stride_state = NO_STRIDE
        self.no_strides_count = 0

        self.last_values = []

        self.coverage_sampled_event = Event()

    async def run_monitor(self):
        while (True):
            await ClockCycles(self.signals['clk'], 1)
            await ReadOnly()

            if self.signals['valid'].value:
                self.last_values.append(int(self.signals['value'].value))

                if len(self.last_values) > 16:
                    self.last_values = self.last_values[1:17]

            if self.signals['stride_1_valid'].value:
                if self.signals['stride_2_valid'].value:
                    self.stride_2_seen[self.signals['stride_1'].value][self.signals['stride_2'].value] += 1
                else:
                    self.stride_1_seen[self.signals['stride_1'].value] += 1

            self.check_latest_strides()
            self.coverage_sampled_event.set()

    def sample_single_stride_coverage(self, single_stride):
        no_stride = True

        if single_stride < STRIDE_MIN:
            self.misc_bins['single_stride_n_overflow'] += 1
        elif single_stride > STRIDE_MAX:
            self.misc_bins['single_stride_p_overflow'] += 1
        else:
            no_stride = False

            if self.stride_state == NO_STRIDE:
                self.misc_bins['no_stride_to_single'] += 1
            elif self.stride_state == DOUBLE_STRIDE:
                self.misc_bins['double_stride_to_single'] += 1

            self.stride_state = SINGLE_STRIDE
            self.no_strides_count = 0

        if no_stride:
            self.no_strides_count += 1

    def sample_double_stride_coverage(self, first_stride, second_stride):
        no_stride = True

        if first_stride < STRIDE_MIN and second_stride < STRIDE_MIN:
            self.misc_bins['double_stride_nn_overflow'] += 1
        if first_stride < STRIDE_MIN and second_stride > STRIDE_MAX:
            self.misc_bins['double_stride_np_overflow'] += 1
        if first_stride > STRIDE_MAX and second_stride < STRIDE_MIN:
            self.misc_bins['double_stride_pn_overflow'] += 1
        if first_stride > STRIDE_MAX and second_stride > STRIDE_MAX:
            self.misc_bins['double_stride_pp_overflow'] += 1
        else:
            no_stride = False
            if self.stride_state == NO_STRIDE:
                self.misc_bins['no_stride_to_double'] += 1
            elif self.stride_state == SINGLE_STRIDE:
                self.misc_bins['single_stride_to_double'] += 1

            self.stride_state = DOUBLE_STRIDE
            self.no_strides_count = 0

        if no_stride:
            self.no_strides_count += 1

    def check_latest_strides(self):
        if (len(self.last_values) < 16):
            return

        value_pairs = list(zip(self.last_values, [None] + self.last_values))
        strides = list(map(lambda x: x[0] - x[1], value_pairs[1:]))

        stride_set = set(strides)
        if len(stride_set) == 1:
            self.sample_single_stride_coverage(next(iter(stride_set)))
        elif len(stride_set) == 2:
            first_strides = [s for (i, s) in enumerate(strides) if i % 2 == 0]
            second_strides = [s for (i, s) in enumerate(strides) if i % 2 == 1]

            first_stride_set = set(first_strides)
            second_stride_set = set(second_strides)

            if len(first_stride_set) == 1 and len(second_stride_set) == 1:
                self.sample_double_stride_coverage(next(iter(first_stride_set)),
                        next(iter(second_stride_set)))
            else:
                self.no_strides_count += 1
        else:
            self.no_strides_count += 1

        if self.no_strides_count > 16:
            self.stride_state = NO_STRIDE



    def output_coverage(self):
        print ("****************** One Stride Bins *************")
        for i in range(STRIDE_MIN, STRIDE_MAX + 1):
            if i < 0:
                stride_offset = NUM_STRIDES + i
            else:
                stride_offset = i

            print (i, self.stride_1_seen[stride_offset])

        print ("****************** Two Stride Bins *************")

        for i in range(STRIDE_MIN, STRIDE_MAX + 1):
            if i < 0:
                stride_offset_1 = NUM_STRIDES + i
            else:
                stride_offset_1 = i

            for j in range(STRIDE_MIN, STRIDE_MAX + 1):
                if i == j:
                    # Where the two strides are the same we'll never see
                    # coverage (as this is the single stride case)
                    continue

                if j < 0:
                    stride_offset_2 = NUM_STRIDES + j
                else:
                    stride_offset_2 = j

                print (i, j, self.stride_2_seen[stride_offset_1][stride_offset_2])

        pprint(self.misc_bins)

    # Flatten all coverage bins into a single vector (python list of integers)
    def get_coverage_vector(self):
        coverage_vector = []

        # Drop the stride_2 bins where both have the same stride from the
        # coverage vector (these will never be covered as they're captured as
        # single strides).
        for i, bins in enumerate(self.stride_2_seen):
            for j, bin_val in enumerate(bins):
                if (i != j):
                    coverage_vector.append(bin_val)

        coverage_vector += self.stride_1_seen
        coverage_vector += self.misc_bins.values()

        return coverage_vector

    def get_coverage_bool_vector(self):
        return [1 if x > 0 else 0 for x in self.get_coverage_vector()]


async def do_reset(dut):
    dut.rst_ni.value = 1
    await Timer(15, units="ns")

    dut.rst_ni.value = 0
    await ClockCycles(dut.clk_i, 3)
    await Timer(5, units="ns")

    dut.rst_ni.value = 1

# Produces the stimulus for the testbench based on observed coverage
class StimulusProducer:
    def __init__(self, dut, coverage_monitor):
        self.dut = dut
        self.coverage_monitor = coverage_monitor
        self.new_value = None
        self.end_simulation_event = Event()

    # Handles driving a new_value when one is provided by `determine_next_value`
    async def drive_new_value(self):
        while(True):
            await ClockCycles(self.dut.clk_i, 1)
            await ReadWrite()

            if self.new_value:
                self.dut.valid_i.value = 1
                self.dut.value_i.value = self.new_value
            else:
                self.dut.valid_i.value = 0
                self.dut.value_i.value = 0xbaaddead

    # Loops observing coverage and from that decides what value to use next for
    # stimulus
    async def determine_next_value(self):
        self.new_value = 1
        current_stride = 1

        # Condition on this loop determines how long the simulation runs for
        while current_stride <= STRIDE_MAX:
            # Waits for coverage sampling to be complete for this clock cycle
            await self.coverage_monitor.coverage_sampled_event.wait()
            self.coverage_monitor.coverage_sampled_event.clear()

            ### Beginning of stimulus determination based on latest coverage
            if self.coverage_monitor.stride_1_seen[current_stride] > 16:
                current_stride += 1

            self.new_value += current_stride
            ### End of stimulus determination based on latest coverage

        # Loop has finished, end the simulation
        self.new_value = None
        self.end_simulation_event.set()

    # Sets off the co-routines that run the StimulusProcessor
    def run_producer(self):
        cocotb.start_soon(self.drive_new_value())
        cocotb.start_soon(self.determine_next_value())

@cocotb.test()
async def basic_test(dut):
    coverage_monitor = CoverageMonitor(dut)
    stimulus_producer = StimulusProducer(dut, coverage_monitor)
    dut.valid_i.value = 0

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())
    await do_reset(dut)
    cocotb.start_soon(coverage_monitor.run_monitor())
    stimulus_producer.run_producer()

    # Wait for end of simulation to be signalled. Give the design a few more
    # clocks to run before outputting final coverage values
    await stimulus_producer.end_simulation_event.wait()
    await ClockCycles(dut.clk_i, 5)

    coverage_monitor.output_coverage()
