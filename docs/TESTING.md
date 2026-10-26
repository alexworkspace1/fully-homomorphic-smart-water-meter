# Testing and Validation

This document sums up how SmartWaterMeter was tested, from the test report (`Senior Design Test Report.pdf`) and the test plan (`Smart Water Testing Document.pdf`). It also says which planned tests exist in the repository.

## How accuracy is validated

The main check compares two values of $Q_d$ for the same day:

1. **Plaintext reference:** `Step1_CS1` computes $Q_d$ from the unencrypted readings in double precision and writes it to `ptxt_res/`.
2. **Encrypted result:** the full pipeline computes $Q_d$ on ciphertexts, and `CheckRes` decrypts and rescales it into `ctxt_res/`.

The difference between the two is the error that encoding and the lookup tables introduce. [SYSTEM_MODELS.md](SYSTEM_MODELS.md#error-budget) estimates its size.

## Tests reported as run

### Unit tests (test report)

| # | Under test | What was checked |
|---|---|---|
| 1 | `OutputPlaintext` | Decrypted `resultDec1`/`resultDec2` from `Step2_TA1` are written in the expected format |
| 2 | `OutVector` | `vecLog`/`vecRecLog` from `Step1_CS1` print in full; the output depends on the table sizes |
| 3 | `PrintParameters` | Each step's SEAL context has the expected BFV parameters |
| 4 | `ShiftWork` (index form) | The PIR row query is shifted correctly. The random form was not tested |
| 5 | `LoadKey` | Keys load into a context created from the saved parameters |
| 6 | `KeyGen.cpp` | All four keys are generated, saved to `Key/`, and load from any context with the same parameters |

These tests were run by hand. There is no test code in the repository.

### Metamorphic tests (test report)

| Relation | Expected | Reported result |
|---|---|---|
| Computational accuracy | AM, HM and $Q_d$ on ciphertexts equal the plaintext values | Passed |
| Scaling | Scaling every input scales AM and HM similarly and leaves $Q_d$ unchanged | Passed |

The scaling relation holds exactly for the values that are averaged: multiplying every $x_i(t)$ by $c$ multiplies both AM and HM by $c$, and $Q_d$ is unchanged. The code averages $x = \ln(w + 2)$, though. Multiplying the raw readings $w$ by $c$ adds roughly $\ln c$ to each $x$ instead of scaling it, so $Q_d$ changes. The test report does not say which values were scaled. A repeat of this test should scale $x$, or expect $Q_d$ to move.

## Tests planned but not in the repository

The test plan describes unit tests (encrypt and decrypt 42, add 42 + 58, multiply 6 × 7, reject a corrupted ciphertext) and integration tests (one meter over a week, many meters, mixed operations). It runs them with scripts under `build/tests/`:

```
./build/tests/unit_test.sh
./build/tests/integration_test.sh
./build/tests/performance_test.sh
./build/tests/regression_test.sh
```

**None of these scripts are in the repository**, and there is no CI. Treat the test plan as a description of intended tests.

## Suggested next tests

| Test | Why |
|---|---|
| End-to-end run on one day, then compare `ptxt_res/` and `ctxt_res/` within a tolerance | The only check of the whole protocol. It would catch known issues 1, 6 and 7 |
| Table-size check: compare the `TABLE_SIZE_*` constants with the entry counts `MakeEncTab_1` prints | Catches known issue 1 at build time |
| Index search on a table where the value is missing, in the last slot, or matches twice | Covers known issue 7 |
| Run with each `MakeEncTab_*` precision level and record error and run time | Measures the precision trade-off the report describes but does not quantify |
| Synthetic attack data: additive, deductive and camouflage changes to some meters | Shows that $Q_d$ actually moves under attack, which is the purpose of the system |
