# LLM for Design Verification

---
___LLM4DV___ is a benchmarking framework utilising large language models in hardware design verification. 
This project provides a framework for incorporating LLMs in test stimuli generation (i.e. 
generating inputs for testing a device). The goal is to generate stimuli to cover most of the test bins 
(i.e. test cases) from a predefined coverage plan with the LLM using as few tokens as possible.

This project contains three device-under-tests (DUTs):
1. __Stride detector__: a device that detects single- and double-stride patterns. 
This kind of design is the core of data prefetchers for CPUs. 
2. __*Ibex* instruction decoder__: a RISC-V instruction decoder.
3. __*Ibex* CPU__: a RISC-V CPU, with instruction and data memory.

This project provides hardware descriptions and various design verification methods for each of the DUTs.

## Getting started

---
The simulation runs as a client-server model. The client side generates stimuli to the server. The server 
side receives stimuli, computes coverage, and returns the DUT state and coverage back to the client.

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

To specify experiment and strategies for stimulus generation on the client side, edit the `generate_stimulus.py` file.

For detailed information, see `README` files of each module.

## Repository structure

---

Detailed structure:
```
.
│  csv_helper.py                       # Utils for processing csv experiment logs
│  flake.loc
│  flake.nix
│  global_shared_types.py              # Wrappers of CoverageDatabase and DUTState
│  main.py                             # Testing script
│  python-requirements.txt
│  README.md
│  stimuli_extractor.py                # Extractor that extracts numbers from text response
│  stimuli_filter.py                   # Filter that filters out invalid numbers
│
├─agents                               # Stimulus producing agent, which incorporate all methods of the client side
│      agents_CLI.py
│      agent_base.py
│      agent_fschat.py
│      agent_IC_dumb.py
│      agent_ID_dumb.py
│      agent_LLM.py
│      agent_random.py
│      agent_SD_dumb.py
│    
├─examples_IC                          # Manually created bin description of Ibex CPU
│      bins_description.txt
│    
├─examples_ID                          # Manually created bin description of Ibex instruction decoder
│      bins_description.txt
│      bins_description_succinct.txt
│      dut_code.txt
│      tb_code.txt
│
├─examples_SD                          # Manually created bin description of stride detector
│      bins_description.txt
│      dut_code.txt
│      tb_code.txt
│
├─examples_SD_analogue                 # Manually created task description, which is an analogue of the stride detector
│      bins_description.txt
│      dut_code.txt
│      tb_code.txt
│
├─experiment_logs                      # Experiment running logs
│  ├─logs_ID_gpt
│  ├─logs_ID_llama2
│  ├─logs_SD_fixed
│  └─logs_SD_template
│
├─ibex_cpu                             # Ibex CPU module
│  │  .flake8
│  │  cocotb_ibex.py
│  │  cocotb_ibex.sv
│  │  generate_stimulus.py
│  │  instructions.py
│  │  instruction_monitor.py
│  │  lint.sh
│  │  Makefile
│  │  mypy.ini
│  │  README.md
│  │  shared_types.py
│  │  test_prog.bin
│  │
│  ├─logs
│  └─src
│
├─ibex_decoder                         # Ibex instruction decoder module
│  │  generate_stimulus.py
│  │  ibex_consts.py
│  │  ibex_decoder.sv
│  │  ibex_decoder_cocotb.py
│  │  ibex_decoder_wrap.sv
│  │  ibex_pkg.sv
│  │  Makefile
│  │  shared_types.py
│  │
│  └─logs
│
├─loggers                              # Logging components of the agent, for logging txt and csv files
│      logger_base.py
│      logger_csv.py
│      logger_txt.py
│
├─models                               # LLM components of the agent, for getting natural language responses from LLMs
│      llm_base.py
│      llm_gpt.py
│      llm_llama2.py
│
├─prompt_generators                    # Prompting components of the agent, for generating question to the LLMs
│      prompt_generator_base.py
│      prompt_generator_fixed_ID.py
│      prompt_generator_fixed_SD.py
│      prompt_generator_template.py
│      prompt_generator_template_IC.py
│      prompt_generator_template_ID.py
│      prompt_generator_template_SD.py
│
└─stride_detector                      # Stride detector module
    │  generate_stimulus.py
    │  Makefile
    │  README.md
    │  shared_types.py
    │  stride_detector.sv
    │  stride_detector_cocotb.py
    │
    └─logs
```

## Reference

---
<!--***-->
