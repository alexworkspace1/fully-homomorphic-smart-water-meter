# System Models

This document gives the formal models behind SmartWaterMeter: the notation, the mathematical model of what is computed, the functional model of the lookup tables, the encoding and precision model, the FHE noise model and the threat model. [ARCHITECTURE.md](ARCHITECTURE.md) describes the components and the protocol that carry these models out.

The equations follow the code in `src/24hour`. The project report (`Senior Design Project.pdf`) states the model on raw readings `w_i(t)`. The code applies a log transform first. Where the two differ, the difference is noted in [Report and implementation](#report-and-implementation).

## Notation

| Symbol | Meaning | In code |
|---|---|---|
| $N$ | Number of smart meters in the region | `METER_NUM = 150` |
| $T$ | Set of hourly time slots in a day, $\lvert T \rvert = 24$ | 24-iteration loops |
| $t$ | One time slot in $T$ | hour index |
| $d$ | One day (date) | `<date>` file suffix |
| $w_i(t)$ | Water usage reported by meter $i$ in slot $t$ | one value of the input file |
| $x_i(t)$ | Log-transformed reading, $x_i(t) = \ln(w_i(t) + 2)$ | `log(*iter2 + 2)` in `Step1_CS1` |
| $AM_t$, $HM_t$ | Arithmetic and Harmonic Mean of slot $t$ | hourly LUT outputs |
| $Q_d$ | Daily HM/AM ratio of day $d$ | `ctxt_res/`, `ptxt_res/` |
| $p_A$, $p_H$ | Precision exponents for per-meter encoding | `PRECISION = 2^5`, `PRECISION2 = 2^10` |
| $s$ | Precision exponent of hourly LUT outputs | $2^9$ in `MakeEncTab_1` |
| $\Delta$ | Base of the digit split | 100 |
| $t_p$ | BFV plain modulus | 786433 |

## Mathematical model

### Statistics per time slot

For each slot $t$, the Arithmetic Mean and Harmonic Mean are taken over the $N$ meters:

$$
AM_t = \frac{1}{N} \sum_{i=1}^{N} x_i(t)
\qquad
HM_t = \frac{N}{\sum_{i=1}^{N} \frac{1}{x_i(t)}}
$$

### Daily ratio

The daily ratio is the sum of the hourly Harmonic Means over the sum of the hourly Arithmetic Means:

$$
Q_d = \frac{\sum_{t \in T} HM_t}{\sum_{t \in T} AM_t}
    = \sum_{t \in T} HM_t \times \frac{1}{\sum_{t \in T} AM_t}
$$

The second form is the one the system evaluates. BFV cannot divide two ciphertexts, so the reciprocal $1 / \sum AM_t$ comes from a lookup table, and the division becomes a multiplication.

### Why the ratio detects tampering

For positive values, $HM_t \le AM_t$, with equality only when every meter in slot $t$ reports the same value (the AM–HM inequality). Therefore $0 < Q_d \le 1$, and $Q_d$ measures how spread out the readings are, not how large they are:

- **Scaling every averaged value** $x_i(t)$ by the same factor scales AM and HM together and leaves $Q_d$ unchanged. The test report's metamorphic test checks this property. Scaling the raw readings $w$ is different: after the log transform it shifts each $x$ instead, so $Q_d$ moves (see [TESTING.md](TESTING.md#metamorphic-tests-test-report)).
- **Additive and deductive attacks** (reporting more or less than the real usage) change the spread of a subset of meters, so $Q_d$ moves.
- **Camouflage attacks** add to some meters and subtract from others to keep $AM_t$ the same. $HM_t$ is more sensitive to small values than $AM_t$, so the ratio still moves.

The log transform $x = \ln(w + 2)$ compresses large readings, and the $+2$ keeps $x > \ln 2 > 0$, so $1/x$ is defined even for a reading of zero.

This document models how $Q_d$ is computed. The project does not include the detector that decides whether a given $Q_d$ is anomalous.

## Lookup-table functional model

A lookup table is a pair of encrypted vectors: an input table $T_{in} = (x_0, \dots, x_{L-1})$ that lists every value an encrypted quantity can take, and an output table $T_{out} = (f(x_0), \dots, f(x_{L-1}))$. Evaluating $f$ on an encrypted $v$ takes three steps:

1. The Computation Server computes $\mathrm{Enc}(v - x_k)$ for every $k$.
2. The Trusted Authority decrypts the differences and finds the index $k^\ast$ with $x_{k^\ast} = v$, or the nearest one.
3. The Computation Server retrieves $\mathrm{Enc}(f(x_{k^\ast}))$ with a PIR query, without learning $k^\ast$.

The report's table of functions maps to the generated tables as follows:

| Report | Quantity | Input $x$ | $f(x)$ | Table files |
|---|---|---|---|---|
| $f_1$ | $HM_t$ | $\sum_i 2^{p_H} / x_i(t)$ | $2^s \cdot N / (x / 2^{p_H})$ | `HM_input`, `HM_output` |
| $f_2$ | $AM_t$ | $\sum_i 2^{p_A} \cdot x_i(t)$ | $2^s \cdot (x / 2^{p_A}) / N$ | `AM_input`, `AM_output` |
| $f_3$, $f_4$ | $\mathcal{H}_1$, $\mathcal{H}_2$ | $\sum_t HM_t$ (scaled) | $\lfloor x / \Delta \rfloor$, $x \bmod \Delta$ | `div_HM_input`, `div_HM_output1/2` |
| $f_5$, $f_6$ | $\mathcal{A}_1$, $\mathcal{A}_2$ | $\sum_t AM_t$ (scaled) | $v = 2^{21} / (x / 2^s)$, then $\lfloor v / \Delta \rfloor$, $v \bmod \Delta$ | `SUM_AM_input`, `inv_SUM_AM_output1/2` |
| $f_7$ | $res_2 / \Delta$ | $res_2$ | $\mathrm{round}(x / \Delta)$ | `inv_100_input`, `inv_100_output` |

The report writes $f_5(x) = x / 100$ for $\mathcal{A}_1$. In the code, the table for $\mathcal{A}_1$ and $\mathcal{A}_2$ first takes the reciprocal of $\sum AM_t$ and then splits it, which is what the polynomial representation below needs.

## Polynomial (digit-split) representation

The scaled product $\sum HM_t \times 1/\sum AM_t$ does not fit in the plaintext space, so both factors are split into two base-$\Delta$ digits:

$$
\sum_{t} HM_t = \mathcal{H}_1 \Delta + \mathcal{H}_2
\qquad
\frac{1}{\sum_{t} AM_t} = \mathcal{A}_1 \Delta + \mathcal{A}_2
$$

$$
\left(\mathcal{H}_1 \Delta + \mathcal{H}_2\right)\left(\mathcal{A}_1 \Delta + \mathcal{A}_2\right)
= \mathcal{H}_1 \mathcal{A}_1 \Delta^2
+ \left(\mathcal{H}_1 \mathcal{A}_2 + \mathcal{H}_2 \mathcal{A}_1\right) \Delta
+ \mathcal{H}_2 \mathcal{A}_2
$$

Dividing by $\Delta^2 = 10000$ and dropping the last term:

$$
res_1 = \mathcal{H}_1 \mathcal{A}_1
\qquad
res_2 = \mathcal{H}_1 \mathcal{A}_2 + \mathcal{H}_2 \mathcal{A}_1
\qquad
\widetilde{Q}_d = res_1 + \frac{res_2}{\Delta}
$$

`Step5_CS3` computes $res_1$ and $res_2$. `Step6_TA3` and `Step7_CS4` evaluate $res_2 / \Delta$ with the `inv_100` table and add $res_1$.

## Encoding and precision model

BFV works on integers modulo $t_p$, so every real quantity is scaled by a power of two and rounded:

| Stage | Encoded value |
|---|---|
| Per-meter AM input | $\mathrm{round}(2^{5} \cdot x_i(t))$ |
| Per-meter HM input | $\mathrm{round}(2^{10} / x_i(t))$ |
| Hourly outputs $AM_t$, $HM_t$ | scaled by $2^{9}$ |
| Reciprocal of $\sum AM_t$ | $2^{21} / \sum AM_t$ |
| Product | $2^{9} \sum HM_t \cdot 2^{21} / \sum AM_t = 2^{30} Q_d$ |
| Decrypted result | $\widetilde{Q}_d \approx 2^{30} Q_d / 10^4$, so `CheckRes` computes $Q_d = \widetilde{Q}_d \cdot 10^4 / 2^{30}$ |

The report gives the per-meter encoding as $v(w_i(t))[k] = \mathrm{Round}(2^{p} \cdot w_i(t))$. The code encodes $\ln(w_i(t) + 2)$, with $p = 5$ for the AM vector and $p = 10$ for the HM vector.

### Plaintext range check

The values below are derived from the table ranges in `MakeEncTab_1` (readings from 50 to 6000, so $x \in [\ln 52, \ln 6002] \approx [3.95, 8.70]$). They show why the digit split is needed and that it fits:

| Quantity | Approximate range | Fits in $t_p = 786433$? |
|---|---|---|
| $\sum_t AM_t$ (real) | 95 – 209 | yes |
| $2^{21} / \sum AM_t$ | 10,000 – 22,000, so $\mathcal{A}_1 \approx$ 100 – 220 | yes |
| $2^{9} \sum_t HM_t$ | 48,600 – 107,000, so $\mathcal{H}_1 \approx$ 486 – 1,070 | yes |
| Undivided product $2^{30} Q_d$ | up to $\approx 1.07 \times 10^9$ | **no**, which is why the digits are split |
| $res_1 = \mathcal{H}_1 \mathcal{A}_1$ | up to $\approx 235{,}000$ | yes |
| $res_2$ | up to $\approx 128{,}000$ | yes |
| $\widetilde{Q}_d$ | up to $\approx 107{,}000$ (since $Q_d \le 1$) | yes |

### Error budget

The encrypted result differs from the plaintext $Q_d$ by:

- **Input rounding:** the per-meter values are rounded to $2^{-5}$ and $2^{-10}$.
- **LUT quantisation:** each table output is rounded to an integer at its own scale.
- **The dropped term** $\mathcal{H}_2 \mathcal{A}_2 / 10^4 < 1$, plus at most $0.5$ from rounding $res_2 / \Delta$.

One unit of $\widetilde{Q}_d$ equals $10^4 / 2^{30} \approx 9.3 \times 10^{-6}$ in $Q_d$. So the last two terms add an error on the order of $10^{-5}$. The input rounding and the hourly output scale dominate the remaining error. `MakeEncTab_2` and `MakeEncTab_3` lower $s$ to $2^{7}$ and $2^{5}$: the tables get smaller and the runs faster, but the error is larger. See [LOOKUP_TABLES.md](LOOKUP_TABLES.md#precision-variants).

## FHE parameter and noise model

| Parameter | Value | Effect |
|---|---|---|
| Scheme | BFV | Exact integer arithmetic modulo $t_p$ |
| `poly_modulus_degree` | 8192 | 8192 slots in two rows of 4096; 128-bit security with the default modulus |
| `coeff_modulus` | `BFVDefault(8192)`, about 218 bits | Noise budget available for multiplications |
| `plain_modulus` | 786433, prime, $\equiv 1 \pmod{16384}$ | Allows batching; bounds every encoded value |

Each ciphertext-by-ciphertext multiplication uses a large part of the noise budget. A LUT retrieval multiplies a rotated row query by the column query, then by an output-table row. The result depends only on the fresh query and the fresh table ciphertexts, not on the ciphertext that was looked up. **Each LUT step therefore resets the multiplicative depth**: the noise of $\mathrm{Enc}(v)$ is used only to compute the differences that the TA decrypts. The deepest chain is two multiplications for a retrieval and one more for $res_1$ and $res_2$, which the default parameters allow. Additions, rotations and the rotate-and-add sums add only a small amount of noise.

## Threat model

| Party | Assumed behaviour | Learns |
|---|---|---|
| Smart meter | Honest; holds only the public key | Its own readings |
| Data collector | Honest-but-curious | Ciphertexts only |
| Computation Server | Honest-but-curious; holds public, relinearization and Galois keys | Ciphertexts only. PIR hides which table entry was used |
| LUT provider | Honest; holds the public key | The table ranges it builds |
| Trusted Authority / utility | Honest-but-curious; the only holder of the secret key | Each decrypted difference vector $v - x_k$. The input tables are in sorted order, so the TA learns the **aggregate** values: the hourly sums over $N$ meters, $\sum AM_t$, $\sum HM_t$, $res_2$ and $Q_d$. It never sees an individual meter's reading |

What the design protects is therefore **individual readings** against every party, and every value against the Computation Server. It does not hide the aggregates from the TA. Randomly rotating the tables before each search would hide even those. `Utility.hpp` contains a `ShiftWork` overload for a random shift, but no program calls it.

The assumptions also rule out collusion between the CS and the TA. A CS holding the secret key could decrypt every reading. In this simulation, every party reads the same `Key/` folder, and some CS programs load the secret key for debugging. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md#security--threat-model).

## Report and implementation

| Topic | Project report | Code |
|---|---|---|
| Value averaged | Raw reading $w_i(t)$ | $\ln(w_i(t) + 2)$ |
| Precision parameter | One $2^{p}$ | $2^{5}$ (AM), $2^{10}$ (HM), $2^{9}$ (hourly outputs), $2^{21}$ (reciprocal) |
| $f_5$ | $x / 100$ | Reciprocal of $\sum AM_t$, then split into digits |
| Last step | `Step7_TA4` | `Step7_CS4`, run by the Computation Server |
| Decrypting party | "Utility provider" | Trusted Authority (`TA`); the same role |
