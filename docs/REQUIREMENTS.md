# Requirements

This document restates the requirements from the project report and traces each one to the code that meets it and to its current status. The status column reflects the code review in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## User requirements

| ID | Requirement (from the report) | Met by | Status |
|---|---|---|---|
| UR-1 | Encrypt usage data so that computations run on ciphertexts and never need to decrypt an individual reading | Meters encrypt in `Step1_CS1`; every CS step works only on ciphertexts | Met in the design. In the simulation some CS programs load the secret key for debugging |
| UR-2 | Encrypt consumption data at the point of collection, then compare the encrypted computation with the original data | `Step1_CS1` writes the plaintext `Q_d` to `ptxt_res/`; `CheckRes` writes the encrypted result to `ctxt_res/` | Met. The comparison of the two files is done by hand |
| UR-3 | Use homomorphic lookup tables to compute the AM/HM ratio | `MakeEncTab_*`, Steps 1–7 | Met, but the table sizes in `SGSimulation.hpp` don't match the generated tables (known issue 1) |
| UR-4 | Compute ratios with LUTs because BFV cannot divide, and simulate the five components: smart meters, data collectors, computation servers, LUT provider, utility provider | See [Parties](ARCHITECTURE.md#parties) | Met. Smart meters and the data collector are simulated inside `Step1_CS1` |
| UR-5 | Demonstrate that encrypted computation keeps its accuracy | `CheckRes` compared with `ptxt_res/` | Reported as passed in the test report. A full run from the current code fails at Step 7 (known issue 6) |

## System requirements

| ID | Requirement | Version | Notes |
|---|---|---|---|
| SR-1 | Microsoft SEAL, for BFV encryption | 4.1.2 exactly, as a shared library | [BUILD.md](BUILD.md) |
| SR-2 | CMake, to build | 3.10 or later | |
| SR-3 | OpenMP, for parallel loops | 18.1.8 used in development | |
| SR-4 | A C++17 compiler | GCC 9.3+ or Clang | From the test plan |
| SR-5 | Memory | 8 GB or more | From the test plan |
| SR-6 | Operating system | macOS or Linux; WSL2 on Windows | Key files are opened without `std::ios::binary`, which breaks on native Windows |

## Non-functional requirements

The test plan (`Smart Water Testing Document.pdf`) adds these goals. The report does not set a target for any of them.

| ID | Goal | Status |
|---|---|---|
| NFR-1 | No plaintext or key leaks in memory, logs or error messages | Not met in the simulation: debug lines print noise budgets, and some decrypt intermediate values |
| NFR-2 | Operations finish within defined performance thresholds | No threshold was defined. The steps print their run times |
| NFR-3 | Invalid or corrupted input is handled gracefully | Not met: missing arguments or files end in an unclear SEAL exception |
| NFR-4 | The system scales to larger data sets | Not measured. Table size grows with the meter count and the precision |
