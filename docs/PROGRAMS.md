# Program Reference

Every program is a standalone executable built from one `.cpp` file in `src/<variant>/`. They communicate only through files: `Key/` and `Table/` are shared inputs, and `Result/` holds the per-day exchange between the Computation Server (CS) and the Trusted Authority (TA). `<dir>` below is the result directory (normally `Result`), `<date>` is a day label such as `2014-01-01`, and `<h>` is an hour `0..23`.

Arguments are positional and are not validated. Missing arguments crash the program.

## Shared headers

| File | Contents |
|---|---|
| `SGSimulation.hpp` | All standard includes, SEAL and OpenMP. Constants: `METER_NUM` (150), `TABLE_SIZE_*` (number of entries in each lookup table), `NF` (OpenMP threads, 16), `PRECISION` (2^5), `PRECISION2` (2^10), and the `Key/` file paths. |
| `Utility.hpp` | Helpers: `LoadKey<T>` (load a key file), `CreateContextFromParams` (rebuild the `SEALContext` from `Key/Params`), `ShiftWork` (rotate a vector to build PIR queries), `PrintParameters`, `PrintExampleBanner`, `OutputPlaintext`, `OutVector`, `PrintVector`, and `ShowMemoryUsage` (Linux only). In `src/24hour` it also contains `ReadData`, `ArithmeticMean` and `HarmonicMean`. In `src/1hour` these live in `Step1_CS1.cpp`. |

## Setup programs

### `KeyGen`
- **Run by:** setup (the TA)
- **Arguments:** none
- **Writes:** `Key/Params`, `Key/PublicKey`, `Key/SecretKey`, `Key/RelinKey`, `Key/GaloisKey`
- Creates the BFV parameters (degree 8192, default coefficient modulus, plain modulus 786433) and all keys. It must run once before anything else, and tables must be regenerated whenever keys are regenerated.

### `MakeEncTab_1` / `MakeEncTab_2` / `MakeEncTab_3` (24-hour only)
- **Run by:** LUT provider
- **Arguments:** none
- **Reads:** `Key/Params`, `Key/PublicKey`
- **Writes:** every file in `Table/` (see [LOOKUP_TABLES.md](LOOKUP_TABLES.md))
- Enumerates every possible input value, computes the matching output, and saves both as encrypted rows of 4096 slots. The three versions differ only in output precision (`2^9`/`2^21`, `2^7`/`2^19`, `2^5`/`2^17`). `script.py` and `CheckRes` assume `MakeEncTab_1`.

## 24-hour pipeline (`src/24hour`)

| # | Program | Arguments | Reads | Writes |
|---|---|---|---|---|
| 1 | `Step1_CS1` | `<data file> <plaintext result file> <dir>` | data file, `Table/AM_input_150`, `Table/HM_input_150` | `<dir>/AM_<h>`, `<dir>/HM_<h>` for `h = 0..23`; appends the plaintext ratio to the result file |
| 2 | `Step2_TA1` | `<dir>` | `<dir>/AM_<h>`, `<dir>/HM_<h>` | `<dir>/pir_AMHM_<h>` |
| 3 | `Step3_CS2` | `<date> <dir>` | `<dir>/pir_AMHM_<h>`, `Table/AM_output_150`, `HM_output_150`, `SUM_AM_input_150`, `div_HM_input_150` | `<dir>/inv_SUM_AM_<date>`, `<dir>/div_HM_<date>` |
| 4 | `Step4_TA2` | `<date> <dir>` | `<dir>/inv_SUM_AM_<date>`, `<dir>/div_HM_<date>` | `<dir>/pir_SUM_AM_DIV_HM_<date>` |
| 5 | `Step5_CS3` | `<date> <dir>` | `<dir>/pir_SUM_AM_DIV_HM_<date>`, `Table/inv_SUM_AM_output{1,2}_150`, `div_HM_output{1,2}_150`, `inv_100_input_150` | `<dir>/Fin_AM1HM1_<date>`, `<dir>/inv_100_<date>` |
| 6 | `Step6_TA3` | `<date> <dir>` | `<dir>/inv_100_<date>` | `<dir>/pir_inv_<date>` |
| 7 | `Step7_CS4` | `<date> <dir>` | `<dir>/pir_inv_<date>`, `<dir>/Fin_AM1HM1<date>` (see Known Issues), `Table/inv_100_output_150` | `<dir>/finalRes_<date>` |
| — | `CheckRes` | `<date> <dir> <ciphertext result file>` | `<dir>/finalRes_<date>` | appends the decrypted ratio to the result file |

### What each step does

1. **`Step1_CS1`**: simulates the meters and the data collector. For each hour and each meter, encrypts `round(2^5·ln(w+2))` and `round(2^10/ln(w+2))` (replicated across all 4096 slots) and adds them up homomorphically. Then subtracts each row of the AM/HM input tables from the hourly sums (the table search). Also computes the plaintext AM, HM and ratio for comparison.
2. **`Step2_TA1`**: decrypts the table-search differences for each hour, finds the matching index (zero, or the nearer side of the sign change), and encrypts a two-part PIR query for the AM and HM index.
3. **`Step3_CS2`**: uses the PIR queries to retrieve the encrypted hourly `AM_t` and `HM_t` from the output tables, sums them over 24 hours, and runs table searches on `ΣAM` (for `1/ΣAM`) and `ΣHM` (to split it into base-100 digits).
4. **`Step4_TA2`**: decrypts the two table searches, finds both indices, and encrypts four PIR query ciphertexts into one file.
5. **`Step5_CS3`**: retrieves `A1, A2` (digits of `2^30/ΣAM`) and `H1, H2` (digits of `ΣHM`), computes `A1·H1` and the cross term `A1·H2 + A2·H1`, prints the noise budget, and runs a table search on the cross term for the divide-by-100 lookup.
6. **`Step6_TA3`**: decrypts the cross-term search, finds the index, and encrypts the PIR query.
7. **`Step7_CS4`**: retrieves `round(cross / 100)`, sums it over all slots, and adds `A1·H1`, giving `Enc(Q_d · 2^30 / 10000)`.
8. **`CheckRes`**: decrypts slot 0 and prints and saves `Q_d = value · 10000 / 2^30`.

### `script.py`
Drives the 24-hour pipeline over every day from 2014-01-01 to 2014-12-30. It runs `make` and `MakeEncTab_1`, then Steps 1–7 and `CheckRes` per day, and clears `Result/` between days. Data is read from `DateWiseData/NormalWinso/2014/<date>.txt`. Results are appended to `ptxt_res/test2014.txt` and `ctxt_res/test2014.txt`.

## 1-hour pipeline (`src/1hour`)

The same protocol, but the hourly part (Steps 1–3) runs once per hour, and Steps 3 and 5 are split into separate AM and HM programs.

| # | Program | Arguments | Reads | Writes |
|---|---|---|---|---|
| 1 | `Step1_CS1` | `<data file> <plaintext result file> <dir> <h>` | data file, `Table/AM_input_150`, `HM_input_150` | `<dir>/AM_<h>`, `<dir>/HM_<h>` |
| 2 | `Step2_TA1` | `<dir> <h>` | `<dir>/AM_<h>`, `<dir>/HM_<h>` | `<dir>/pir_AM_<h>`, `<dir>/pir_HM_<h>` |
| 3a | `Step3_CS2_1` | `<date> <dir> <h>` | `<dir>/pir_AM_<h>`, `<dir>/sumAM_<h-1>`, `Table/AM_output_150`; at `h = 23` also `Table/SUM_AM_input_150` | `<dir>/sumAM_<h>` (for `h < 23`); at `h = 23`: `<dir>/inv_SUM_AM_<date>` |
| 3b | `Step3_CS2_2` | `<date> <dir> <h>` | `<dir>/pir_HM_<h>`, `<dir>/sumHM_<h-1>`, `Table/HM_output_150`; at `h = 23` also `Table/div_HM_input_150` | `<dir>/sumHM_<h>` (for `h < 23`); at `h = 23`: `<dir>/div_HM_<date>` |
| 4 | `Step4_TA2` | `<date> <dir>` | `<dir>/inv_SUM_AM_<date>`, `<dir>/div_HM_<date>` | `<dir>/pir_SUM_AM_DIV_HM_<date>` |
| 5a | `Step5_CS3_1` | `<date> <dir>` | `<dir>/pir_SUM_AM_<date>`, `Table/inv_SUM_AM_output{1,2}_150` | `<dir>/AM1AM2_<date>` |
| 5b | `Step5_CS3_2` | `<date> <dir>` | `<dir>/pir_DIV_HM_<date>`, `Table/div_HM_output{1,2}_150` | `<dir>/HM1HM2_<date>` |
| 5c | `Step5_CS3` | `<date> <dir>` | `<dir>/AM1AM2_<date>`, `<dir>/HM1HM2_<date>`, `Table/inv_100_output_150` | `<dir>/Fin_AM1HM1_<date>`, `<dir>/inv_100_<date>` |
| 6 | `Step6_TA3` | `<date> <dir>` | `<dir>/inv_100_<date>` | `<dir>/pir_inv_<date>` |
| 7 | `Step7_CS4` | `<date> <dir>` | `<dir>/pir_inv_<date>`, `<dir>/Fin_AM1HM1_<date>`, (intended) `Table/inv_100_output_150` | `<dir>/finalRes_<date>` |
| — | `CheckRes` | `<date> <dir> <ciphertext result file>` | `<dir>/finalRes_<date>` | appends the decrypted ratio |

`run.sh` runs `cmake`, `make`, `KeyGen` and `Step1_CS1`. It passes no arguments to `Step1_CS1`, so that step needs to be run by hand.

The 5a/5b inputs (`pir_SUM_AM_*`, `pir_DIV_HM_*`) do not match the file Step 4 writes (`pir_SUM_AM_DIV_HM_*`). This and other 1-hour mismatches are listed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
