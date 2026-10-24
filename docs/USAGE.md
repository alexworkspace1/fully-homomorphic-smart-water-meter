# Usage

Build the project first ([BUILD.md](BUILD.md)). All commands below run from inside the variant folder (`src/24hour` or `src/1hour`), because the programs use relative paths.

### Working directories

None of these folders are in the repository. Create them before the first run:

```bash
mkdir -p Key Table Result ptxt_res ctxt_res
```

| Folder | Contents | Written by |
|---|---|---|
| `Key/` | `Params`, `PublicKey`, `SecretKey`, `RelinKey`, `GaloisKey` | `KeyGen` |
| `Table/` | Encrypted lookup tables, suffixed with `_150` (`METER_NUM`) | `MakeEncTab_*` |
| `Result/` | Intermediate ciphertexts and PIR queries for one day | Steps 1–7 |
| `ptxt_res/` | Plaintext reference ratio per day | `Step1_CS1` |
| `ctxt_res/` | Ratio computed through the encrypted pipeline per day | `CheckRes` |

Keys, tables and results are large binary files and must **not** be committed.

### Input data

The dataset is not included in the repository; the project was given permission to use it only for a specific period. `script.py` expects one file per day:

```
DateWiseData/NormalWinso/2014/YYYY-MM-DD.txt
```

Each file is comma-separated text:

```
TimeSlot,<meter 1 id>,<meter 2 id>,...,<meter 150 id>
<slot label>,<usage>,<usage>,...,<usage>
...                                    (24 rows, one per hour)
```

- The row whose first field is `TimeSlot` is the header and is skipped.
- Every other row has a time-slot label followed by `METER_NUM` (150) usage readings.
- Rows are stored in a `std::map` keyed by the label, so they are processed in **lexicographic** label order. Use zero-padded labels (`00`, `01`, … `23`) so the order matches the hour order.
- The lookup tables cover per-hour averages of `ln(w + 2)` between `ln(52)` and `ln(6002)`, i.e. typical readings of roughly 50–6000 units.

### Running the 24-hour variant

`src/24hour/script.py` automates the whole process for each day of 2014. Run the steps by hand for a single day like this:

```bash
DATE=2014-01-01
DATA=DateWiseData/NormalWinso/2014/$DATE.txt

./bin/KeyGen                                   # once
./bin/MakeEncTab_1                             # once per key set (slow)

./bin/Step1_CS1 $DATA ptxt_res/test2014.txt Result
./bin/Step2_TA1 Result
./bin/Step3_CS2 $DATE Result
./bin/Step4_TA2 $DATE Result
./bin/Step5_CS3 $DATE Result
./bin/Step6_TA3 $DATE Result
./bin/Step7_CS4 $DATE Result
./bin/CheckRes  $DATE Result ctxt_res/test2014.txt

rm -rf Result && mkdir Result                  # clear before the next day
```

`script.py` writes `"<day index>,"` to both result files before each day, so every line ends up as `index,ratio`. Compare `ptxt_res/test2014.txt` with `ctxt_res/test2014.txt` line by line to measure the accuracy of the encrypted computation.

> **Note:** `script.py` currently contains debugging `exit(0)` calls (after Step 1 and at the end of the loop). Remove them locally to run the full pipeline. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

### Running the 1-hour variant

This variant has no table generator. Copy the `Table/` folder produced in `src/24hour` (with the same `Key/` folder; tables only work with the keys they were encrypted with).

Steps 1–3 run once per hour, in order, for `HOUR = 0..23`. Step 3 keeps a running encrypted total in `Result/sumAM_<HOUR>` / `sumHM_<HOUR>`. At hour 23 it writes the inputs for Step 4.

```bash
DATE=2014-01-01
DATA=DateWiseData/NormalWinso/2014/$DATE.txt

for HOUR in $(seq 0 23); do
  ./bin/Step1_CS1   $DATA ptxt_res/test2014.txt Result $HOUR
  ./bin/Step2_TA1   Result $HOUR
  ./bin/Step3_CS2_1 $DATE Result $HOUR
  ./bin/Step3_CS2_2 $DATE Result $HOUR
done

./bin/Step4_TA2   $DATE Result
./bin/Step5_CS3_1 $DATE Result
./bin/Step5_CS3_2 $DATE Result
./bin/Step5_CS3   $DATE Result
./bin/Step6_TA3   $DATE Result
./bin/Step7_CS4   $DATE Result
./bin/CheckRes    $DATE Result ctxt_res/test2014.txt
```

`Step1_CS1` appends the plaintext ratio to `ptxt_res/test2014.txt` on every call, so in this variant the file gets 24 lines per day.

> **Note:** the 1-hour variant has several file-name and logic mismatches between steps that stop it from completing in its current state. Check [KNOWN_ISSUES.md](KNOWN_ISSUES.md) before relying on its output.

### Reading the output

Each program prints its progress and timing, for example `Whole runtime is: 12.3s`. On Linux it also prints memory usage from `/proc/<pid>/status`. The key lines are:

- `Step1_CS1`: `Plaintext result >> AM: …, HM: …` for each hour, then `ratio result: …` (the plaintext `Q_d`).
- TA steps: `IndexRow…, IndexCol…` — the lookup-table position that was found — or `ERROR: … Not Found` if the value is outside the table.
- `Step5_CS3`: the remaining noise budget in bits. If it reaches 0, decryption returns garbage.
- `CheckRes`: `Final Result: …` (the encrypted-pipeline `Q_d`).
