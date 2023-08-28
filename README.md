# LLM for Design Verification

---
___LLM4DV___ is a benchmark for utilising large language models in hardware design verification. 
This project provides a workflow for incorporating LLMs in stimuli generation (i.e. 
generating inputs for testing a device). The goal is to generate stimuli to cover most of the test bins 
(i.e. test cases) with the LLM generating tokens as few as possible.

This project contains two device-under-test:
1. __Stride detector__: a device that detects single- and double-stride patterns. 
This kind of design is the core of prefetchers for CPUs. 
2. __*Ibex* instruction decoder__: a RISC-V instruction decoder.

This project provides hardware descriptions and various design verification methods for each of the DUTs.

## Getting started

---
The simulation runs as a client-server model. The client side generates stimuli to the server. The server 
side receives stimuli, computes bin coverage, and returns the coverage back to the client.

### Software pre-requisites

You will need to install __cocotb__, you can find the installation guide here:
https://docs.cocotb.org/en/stable/install.html

Additionally, you'll need the dependencies listed in `python-requirements.txt`
which can be installed with pip:

> pip install --user -r python-requirements.txt

(These requirements are needed for both the client and server)

__Verilator__ is used as the simulator. Pre-built binary packages are often out of
date and a recent (v5 onwards) version of verilator is required, so it is
recommended you build the latest stable tag (v5.012 at time of writing) from
source as described here:
https://verilator.org/guide/latest/install.html#detailed-build-instructions

You may also want __GTKWave__: https://gtkwave.sourceforge.net/, this allows you to
view the waveform output from a simulator run. Again it is recommended you build
this from source. Note this is strictly optional and you may not have any need
for it at all.

### Running the simulation

1. Run `make` for the server and `generate_stimulus.py` for the client in the module's directory.
   + You may need to run `make` under a Python venv.
2. Specify port / IP address & port when the server and client processes start.
3. Running logs will be stored as txt and csv files in `./[module]/logs` as default.

To specify stimulus generation methods on the client side, edit the `generate_stimulus.py` file.

For detailed information, see `README` files of each module.

## Repository structure

---
```bash
.
├─agents                    # Stimulus producing agent, which incorporate all methods of the client side
├─examples_ID               # Manually created bin description of Ibex instruction decoder
├─examples_SD               # Manually created bin description of stride detector
├─examples_SD_analogue      # Manually created task description, which is an analogue of the stride detector
├─experiment_logs           # Experiment running logs
│  ├─logs_ID_llama2
│  ├─logs_SD_fixed
│  └─logs_SD_template
├─ibex_decoder              # Ibex instruction decoder module
│  └─logs
├─loggers                   # Logging components of the agent, for logging txt and csv files
├─models                    # LLM components of the agent, for getting natural language responses from LLMs
├─prompt_generators         # Prompting components of the agent, for generating question to the LLMs
└─stride_detector           # Stride detector module
    └─logs
```