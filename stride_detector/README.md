# Introduction

This directory contains a simple RTL design for a 'stride detector'. It looks at
an incoming stream of values and determines if they increasing/decreasing by
some fixed amount, the stride. It can detect single and double strides (where
the value increases/decreases by one fixed value and then another fixed value in
an alternating manner).

For example the values 1,2,3,4,5,6 have a single stride of +1, the values of
2,4,6,8,10 have a single stride of +2. The values of 1,2,4,5,7,8,10 have a
double stride of +1, +2.

The detector can only work with a certian range of strides, those that can be
expressed with a 2s complement 5 bit integer, that is -16 to 15. When values
have a single or double stride pattern with strides outside that range it cannot
detect them (they're referred to as overflows in the coverage).

This kind of design is at the core of simpler data prefetchers for CPUs, however
this is not relevant to the example.

The cocotb testbench stimulates the stride detector and gathers coverage on its
behaviour. Details are in the comments in the file.

# Software pre-requisites

You will need to install cocotb, you can find the install guide here:
https://docs.cocotb.org/en/stable/install.html

Additionally you'll need the dependcies listed in 'python-requirements.txt'
which can be installed with pip:

> pip install --user -r python-requirements.txt

(These requirements are needed for both the client and server)

Verilator is used as the simulator. Pre-built binary packages are often out of
date and a recent (v5 onwards) version of verilator is required so it is
recommened you build the latest stable tag (v5.012 at time of writing) from
source as described here:
https://verilator.org/guide/latest/install.html#detailed-build-instructions

You may also want GTKWave: https://gtkwave.sourceforge.net/, this allows you to
view the waveform output from a simulator run. Again it is recommended you build
this from source. Note this is strictly optional and you may not have any need
for it at all.

# Running the simulation

A client/server model is used where the server runs the simulation and the
cocotb testbench and the client provides stimulus. For every new piece of
stimulus sent from the client the server responds with the latest coverage
following the stimulus being used and the full DUT state at the time the
stimulus was applied.

The client is a stand-alone python program. Note that the client and server do
not have to run in the same python environment.

The simulation server is driven through a Makefile. It defines a few variables
and then includes a makefile from cocotb which actually runs everything. Simply
run 'make' to build the testbench and start the server. When the 'running
basic_test' message is seen run the client in a new shell on the same machine
('./generate_stimulus.py')

If everything works after a short while you will see a report from cocotb
indicating a test pass from the server. Before that information you will see a
dump of the coverage information. This final few lines should look like this:

15 1 0
15 2 0
15 3 0
15 4 0
15 5 0
15 6 0
15 7 0
15 8 0
15 9 0
15 10 0
15 11 0
15 12 0
15 13 0
15 14 0
{'double_stride_nn_overflow': 0,
 'double_stride_np_overflow': 0,
 'double_stride_pn_overflow': 0,
 'double_stride_pp_overflow': 0,
 'double_stride_to_single': 0,
 'no_stride_to_double': 0,
 'no_stride_to_single': 0,
 'single_stride_n_overflow': 0,
 'single_stride_p_overflow': 0,
 'single_stride_to_double': 0}
  1260.00ns INFO     cocotb.regression                  basic_test passed
  1260.00ns INFO     cocotb.regression                  *******************************************************************************************
                                                        ** TEST                               STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                                                        *******************************************************************************************
                                                        ** stride_detector_cocotb.basic_test   PASS        1260.00           0.03      37140.72  **
                                                        *******************************************************************************************
                                                        ** TESTS=1 PASS=1 FAIL=0 SKIP=0                    1260.00           0.38       3291.29  **
                                                        *******************************************************************************************


The simulation outs a 'dump.fst' file. This is the waveform that you can view
with gtkwave.

# The initial task

The aim here is to find stimulus to cover all of the coverage bins. Doing this
manually is a fairly trivial task but we are interested in AI technqiues to
achieve it.

The provided 'generate_stimulus.py'has a very basic coverage directed stimulus
generation mechanism which doesn't employ AI. It generates values with a single
stride. It waits til it's seen a coverage bin indicating that single stride has
been seen and then moves on to generating values with another stride until we've
seen all single strides from 1 to 15.

# Notes

Verilog scheduling semantics are complex and it's easy to sample and drive
values at the wrong point producing race conditions and undefined/strange
behaviour. The testbench server has been constructed to deal with this so
ideally avoid modifying it.

If modifications are required care must be taken when you're dealing with the
DUT directly (that is reading or writing any of the signals available under the
'dut' value that `basic_test` gets as an argument).  You may want to discuss
what you want to do first so we can look at possible race conditions and how to
deal with them.

Coverage is provided via a 'CoverageDatabase' object defined in
'shared_types.py'. You can read the bins directly but for ML purposes a
`get_coverage_vector` method is provided. This takes the structured coverage and
flattens it into a single list of integers. Not useful for human analysis but
useful for driving a training/evaluation process.

The state of the DUT is provided via a 'DUTState' object. The names of fields in
this object directly map to flops (registers, clocked state holding elements) in
the RTL. A `state_vector` method is provided that maps this state into a list of
integers.

Whilst the state is represented as integers each part of the state has a
different set of valid values, these are described in the comments of
shared_types.py

A `get_coverage_bool_vector` is also provided. This just turns the integers from
`get_coverage_vector` into either 0 or 1 depending on whether the coverage bin
value is non-zero. In general we don't care too much about how many times a bin
has been hit, but rather that we have hit every bin. So the bool version of the
vector may be more suitable for use in training/evaluation.
