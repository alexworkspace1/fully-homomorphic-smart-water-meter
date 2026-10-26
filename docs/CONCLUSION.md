# Conclusion

## Summary

SmartWaterMeter shows that a water utility can compute an analytic over a whole region — the daily ratio of the Harmonic Mean to the Arithmetic Mean, $Q_d$ — while each meter's reading stays encrypted from the meter to the final result. It does this with the BFV scheme in Microsoft SEAL and a lookup-table protocol with Private Information Retrieval (LUT + PIR), adapted from earlier work on smart electricity grids.

## What the project achieved

- **Privacy for individual readings.** Meters encrypt at the source. The Computation Server does every computation on ciphertexts and never holds the secret key. The Trusted Authority decrypts only aggregate differences, never a single meter's reading. See the [threat model](SYSTEM_MODELS.md#threat-model).
- **Operations BFV lacks.** Division, reciprocals and rescaling, which BFV cannot compute, are evaluated with lookup tables. PIR hides from the server which table entry was used.
- **Plaintext overflow handled.** Splitting both factors into base-100 digits keeps every intermediate value inside the plain modulus 786433, at the cost of an error on the order of $10^{-5}$ in $Q_d$. See the [precision model](SYSTEM_MODELS.md#encoding-and-precision-model).
- **Noise kept bounded.** Each lookup restarts from fresh query and table ciphertexts, so the multiplicative depth never grows past three, and the default 8192-degree parameters are enough.
- **An accuracy check built in.** Every run produces both a plaintext and an encrypted $Q_d$, so their difference can be measured directly. The test report records that the encrypted results matched.

## Limitations

| Limitation | Effect |
|---|---|
| The TA learns aggregate values | The input tables are in sorted order, so a decrypted difference reveals the hourly and daily sums. Individual readings stay hidden |
| Simulated on one machine | All parties share the `Key/` folder, and some CS programs load the secret key for debugging. Party separation is by convention only |
| Known correctness bugs | Table sizes, index search and file names (see [KNOWN_ISSUES.md](KNOWN_ISSUES.md)) stop a full run of the code as committed. The 1-hour pipeline does not complete |
| No anomaly detector | The system computes $Q_d$ but does not decide whether a value is anomalous |
| Fixed scale | Tables are built for 150 meters and readings from about 50 to 6000. Changing either means regenerating the tables and updating the size constants |
| One data set, one year | Results come from one permitted data set for 2014 |
| Accuracy and speed not quantified | Neither the report nor the test report gives error or run-time figures |
| No automated tests | The test scripts in the test plan are not in the repository |

## Future work

The report names three directions: scale the LUT and PIR steps to larger data sets, compute more advanced metrics, and apply the approach to other utilities. To get there, work in roughly this order:

1. **Make the pipeline run end to end.** Fix the known correctness issues, starting with the table sizes (issue 1) and the Step 7 file name (issue 6). Add an end-to-end test that compares `ptxt_res/` with `ctxt_res/` (see [TESTING.md](TESTING.md#suggested-next-tests)).
2. **Measure the trade-offs.** Record error and run time for each precision level and for several meter counts. This turns the report's qualitative precision discussion into numbers.
3. **Separate the parties.** Give each party its own key folder, remove secret-key loading from CS programs, and exchange ciphertexts over a network instead of through files.
4. **Hide the aggregates from the TA.** Randomly rotate or permute the tables before each search. The code already has a `ShiftWork` overload for a random shift that no program calls.
5. **Close the loop with detection.** Add a detector that flags a day whose $Q_d$ falls outside its normal range, and test it on synthetic additive, deductive and camouflage attacks.
6. **Reduce duplication.** Merge the 1-hour and 24-hour variants and the near-identical `_1`/`_2` programs, so a fix is made only once.
7. **Explore other schemes.** CKKS computes on approximate real numbers and could remove the integer scaling and some of the lookups. Compare its accuracy and speed with the BFV pipeline.

## Final remarks

The project's central idea holds up: lookup tables and PIR give a BFV pipeline the division it lacks, and keep noise bounded while doing it. The implementation is a research prototype. Once the steps above make it run reliably, it is a sound base for measuring how far privacy-preserving analytics on a smart water grid can scale.
