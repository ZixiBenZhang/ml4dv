# Introduction

[`shared_types.py`]: shared_types.py

This directory contains the RTL design of the *Ibex RISC-V Core*.
The simulation is run using
[the same method](../stride_detector/README)
as the stride detector.


The test bench allows you to provide a list of address
and the values to update them to at each clock cycle (timestep).
One can provide an empty list to advance
the simulation without a changing the memory.
The only other stimulus is a switch to finish the simulation.

[`shared_types.py`][]:
```py
@dataclass
class Stimulus:
    insn_mem_updates: list[tuple[int, int]]
    finish: bool
```

The simulator returns
the last instruction and last program counter value,
as well as the coverage database,
at each clock cycle (timestep).

[`shared_types.py`][]:
```py
@dataclass
class CoverageDatabase:
    instructions: dict[Instr, dict[Cov, int]]
    cross_coverage:  dict[Instr, dict[tuple[Instr, Cov], int]]

# ...

@dataclass
class IbexStateInfo:
    last_pc: Optional[int]
    last_insn: Optional[int]
```

A description of the cover points can be found
in [`instructions.py`](instructions.py):

```py
class Cov(Enum):
    """Coverage Types

    Instruction Coverpoints:
      seen: Has been observed.
      zero_dst: The destination register has been `x0`.
      zero_src: A source register has been `x0`.
      same_src: Two source registers have been the same.
      br_backwards: Has caused a branch backwards.
      br_forwards: Has caused a branch forwards.

    Cross Instruction Coverpoints:
      raw_hazard: Reads from  a register the previous instruction wrote to.
    """
    SEEN = 'seen'
    ZERO_DST = 'zero_dst'
    ZERO_SRC = 'zero_src'
    SAME_SRC = 'same_src'
    BR_BACKWARDS = 'br_backwards'
    BR_FORWARDS = 'br_forwards'
    RAW_HAZARD = 'raw_hazard'
```
