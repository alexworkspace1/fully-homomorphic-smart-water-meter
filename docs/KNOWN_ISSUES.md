# Known Issues

These issues were found in a code review (October 2026) and have **not been fixed yet**. The list is grouped by impact. Line numbers refer to the current `main` branch.

## Correctness

| # | Location | Issue |
|---|---|---|
| 1 | `src/*/SGSimulation.hpp` (`TABLE_SIZE_*`) | The table sizes do not match what `MakeEncTab_1` generates. For example, `AM_input` has ≈22,800 entries (6 rows), but `TABLE_SIZE_AM = 2850` makes every reader load only `ceil(2850/4096) = 1` row. The table files in git history have about 6 and 15 ciphertexts, which agrees. Sums outside the first row are "not found". See [LOOKUP_TABLES.md](LOOKUP_TABLES.md#keeping-tables-and-code-in-sync). |
| 2 | `src/1hour/Step7_CS4.cpp:29` | `readtable_part1` is never opened before the output table is loaded. The 24-hour version opens `Table/inv_100_output_150`. |
| 3 | `src/1hour/Step5_CS3.cpp:84` | The table search loads `inv_100_output_150`. It should be `inv_100_input_150`, as in `src/24hour/Step5_CS3.cpp:211`. |
| 4 | `src/1hour/Step3_CS2_1.cpp:128` | `for (int64_t j1; …)`: the loop counter is never initialized (undefined behaviour). `Step3_CS2_2` uses `= 0`. |
| 5 | `src/1hour/Step5_CS3_1.cpp`, `Step5_CS3_2.cpp` | They read `pir_SUM_AM_<date>` and `pir_DIV_HM_<date>`, but `Step4_TA2` writes a single `pir_SUM_AM_DIV_HM_<date>`. |
| 6 | `src/24hour/Step7_CS4.cpp:109` | It reads `Fin_AM1HM1` + date without the underscore, but `Step5_CS3` writes `Fin_AM1HM1_<date>`. |
| 7 | `Step2_TA1`, `Step4_TA2`, `Step6_TA3` (index search) | `break` exits only the inner loop. The `== 0` check doesn't test the found flag, so a later match can overwrite the first. `[j + 1]` at the end of a row reads the second batch row. If nothing matches, the index variables stay uninitialized and an invalid query is still encrypted and saved, with exit code 0. |
| 8 | `Step1_CS1` (both variants) | Hours are stored in `std::map<std::string, …>`, so labels sort as text (`"10"` before `"2"`). Exactly 24 slots are allocated, with no check on the number of rows. |
| 9 | `src/24hour/MakeEncTab_*.cpp:379` (inv_100 range) | The range is computed as `HM1_max * AM2_max + HM2_max + AM1_max`, but the comment and the use in Step 5 are `HM1·AM2 + HM2·AM1`. Check that the table covers the real cross-term range. |
| 10 | `src/24hour/script.py:44, 79` | Leftover `exit(0)` calls stop the run after Step 1 of the first day. The date range ends on 2014-12-30, and the comment about 2/29 does not apply to 2014. |
| 11 | `CheckRes.cpp` | The `10000 / 2^30` rescale is hard-coded and matches only `MakeEncTab_1`. |

## Security / threat model

- **CS programs load the secret key.** `src/1hour/Step5_CS3.cpp`, `Step5_CS3_1.cpp`, `Step5_CS3_2.cpp` and `src/24hour/Step5_CS3.cpp` load `Key/SecretKey`, print noise budgets, and in some cases decrypt intermediate values. In the intended model only the TA holds the secret key. These lines are for debugging only.
- **One shared `Key/` folder.** Every party reads the same folder, so CS/TA separation exists only by convention.
- **Keys were committed in the past.** `src/*/Key/` (including `SecretKey`) is in the git history. Treat those keys as public and generate new ones with `KeyGen`.
- `src/1hour/Utility.hpp` loads keys with `unsafe_load`, and the 24-hour version uses `load`. Key and query files are sometimes opened without `std::ios::binary`, which breaks on Windows.

## Performance

- `src/1hour/Step5_CS3_1.cpp` / `_2.cpp` make 4096 copies of a ciphertext and rotate each one, which uses several GB of memory. The log-step rotate-and-add used in Step 3 needs only `log2(4096) = 12` rotations.
- The 1-hour `Step1_CS1` encrypts all 24 hours on every call but uses only the requested hour.
- `src/1hour/Step6_TA3.cpp:77` prints a debug line for every slot it checks.
- `relinearize_inplace` is called after additions and rotations, where it does nothing. Only calls after multiplication are needed.
- `NF 16` hard-codes the OpenMP thread count.

## Build and repository

- `CMakeLists.txt` hard-codes Homebrew LLVM 18.1.6 paths, sets the compiler after `project()`, and calls `project()` twice (`SEALExamples`, a leftover from the SEAL examples). See [BUILD.md](BUILD.md) for workarounds.
- Generated files are tracked: `CMakeCache.txt`, `Makefile`, `cmake_install.cmake`, and `.vscode/` with absolute paths from a developer's machine.
- `.gitignore` covers only macOS system files. `Key/`, `Table/`, `Result/`, `bin/`, `CMakeFiles/`, `ptxt_res/` and `ctxt_res/` should be ignored.
- The git history is ≈152 MB because keys, tables and binaries were committed and later deleted.
- `src/1hour` and `src/24hour` are near-copies of each other, as are `Step3_CS2_1/_2`, `Step5_CS3_1/_2` and the three `MakeEncTab_*`. Fixes must be applied in several places.
- `Utility.hpp` defines non-`inline` functions in a header. `PrintVector` calls `resize` on a `const` vector, so it does not compile if it is ever used.
- Program arguments and file opens are not checked. Missing arguments or folders crash with an unclear SEAL exception.
- There are no automated tests or CI. `Smart Water Testing Document.pdf` refers to `build/tests/*.sh` scripts that are not in the repository.
- There is no `LICENSE` file.
