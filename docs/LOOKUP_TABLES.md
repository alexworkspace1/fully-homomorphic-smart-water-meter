# Lookup Tables

BFV cannot divide or compute reciprocals, so the pipeline uses encrypted lookup tables (LUTs) for every non-polynomial step. `MakeEncTab_1` (in `src/24hour`) generates all of them. Each table is a pair, or set, of files in `Table/` with the suffix `_<METER_NUM>`, which is `_150` by default.

### Format

- Each file is a sequence of serialized SEAL ciphertexts, one per *row*.
- A row holds 4096 values in the first batch row of the plaintext (`poly_modulus_degree / 2`). The second batch row is zero.
- Entry `k` is stored in row `k / 4096`, column `k % 4096`.
- The last row is padded with a sentinel value outside the valid range, so a table search never matches the padding.
- An *input* table and its *output* table(s) have the same layout, so the index found in the input table selects the matching output.

### Tables

Values below are for `MakeEncTab_1` with `N = METER_NUM = 150`. The entry counts are approximate.

| Used in | Input table | Output table(s) | Input range | Output | Entries |
|---|---|---|---|---|---|
| Step 1 → 3 | `AM_input` (pad 50000) | `AM_output` (pad 500) | `2^5·N·ln(52)` … `2^5·N·ln(6002)` (≈18,965 – 41,759): the sum over meters of the scaled `ln(w+2)` | `round(2^9 · (x/2^5) / N)`: hourly `AM_t`, scaled by `2^9` | ≈22,800 (6 rows) |
| Step 1 → 3 | `HM_input` (pad 10000) | `HM_output` (pad 500) | `2^10·N/ln(52)` down to `2^10·N/ln(6002)` (≈38,873 – 17,656): the sum over meters of the scaled `1/ln(w+2)` | `round(2^9 · N / (x/2^10))`: hourly `HM_t`, scaled by `2^9` | ≈21,200 (6 rows) |
| Step 3 → 5 | `SUM_AM_input` (pad 60000) | `inv_SUM_AM_output1`, `inv_SUM_AM_output2` (pad 1) | `24·min(AM_output)` … `24·max(AM_output)`: `ΣAM` over the day | `v = round(2^21 / (x/2^9))`, split as `output1 = v / 100`, `output2 = v % 100` | ≈58,000 (15 rows) |
| Step 3 → 5 | `div_HM_input` (pad 60000) | `div_HM_output1` (pad 600), `div_HM_output2` (pad 1) | `24·min(HM_output)` … `24·max(HM_output)`: `ΣHM` over the day | `x / 100` and `x % 100` (splits `ΣHM` into base-100 digits) | ≈58,000 (15 rows) |
| Step 5 → 7 | `inv_100_input` (pad 60000) | `inv_100_output` (pad 1) | Range of the cross term `A1·H2 + A2·H1` | `round(x / 100)` | depends on the digit ranges |

### Precision variants

| Generator | Hourly AM/HM output scale | `1/ΣAM` numerator | Final scale in `CheckRes` |
|---|---|---|---|
| `MakeEncTab_1` | `2^9` | `2^21` (`v = 2^30 / ΣAM`) | `10000 / 2^30` (as written) |
| `MakeEncTab_2` | `2^7` | `2^19` | would need `10000 / 2^26` |
| `MakeEncTab_3` | `2^5` | `2^17` | would need `10000 / 2^22` |

Lower precision gives smaller tables and faster runs but a less accurate ratio. Only `MakeEncTab_1` matches the constant currently in `CheckRes`.

### Keeping tables and code in sync

The programs that read the tables do not read their length from the file. They compute the row count from the `TABLE_SIZE_*` constants in `SGSimulation.hpp`:

```cpp
#define TABLE_SIZE_AM      2850
#define TABLE_SIZE_HM      2653
#define TABLE_SIZE_AM_INV  3647
#define TABLE_SIZE_100_INV 3647
#define TABLE_SIZE_DIV_HM  7935
```

These must match the entry counts that `MakeEncTab_*` actually produces. `MakeEncTab_1` prints each table's size (`InputArith table size is: …`, `Size: …`, `inv100 size: …`) when it runs. After changing `METER_NUM`, the precision, or the generator, update the constants from that output. With the current values they do **not** match (see [KNOWN_ISSUES.md](KNOWN_ISSUES.md)).

Tables are encrypted with the public key in `Key/`. Running `KeyGen` again makes every existing table unusable, so regenerate the tables after it.
