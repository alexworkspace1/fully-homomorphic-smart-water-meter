# Glossary

| Term | Meaning |
|---|---|
| **AM** (Arithmetic Mean) | The sum of values divided by their count. Here, the mean of $\ln(w + 2)$ over the meters in one time slot |
| **AMI** (Advanced Metering Infrastructure) | Smart meters, communication networks and data-management systems that let a utility monitor usage remotely |
| **Additive attack** | Reporting more usage than was consumed |
| **Batching / SIMD** | Packing many values into the slots of one ciphertext so that one operation acts on all of them (Single Instruction, Multiple Data) |
| **BFV** (Brakerski–Fan–Vercauteren) | An FHE scheme for exact addition, subtraction and multiplication of integers modulo a plain modulus |
| **Camouflage attack** | Changing some meters up and others down so that the mean stays the same |
| **Ciphertext** | Encrypted data |
| **CS** (Computation Server) | The party that does all homomorphic computation. It never holds the secret key |
| **Data collector** | Gathers ciphertexts from the meters of a region and forwards them to the CS |
| **Deductive attack** | Reporting less usage than was consumed (water theft) |
| **Differential Privacy** | Protecting individuals by adding calibrated noise to results |
| **Digit split** | Writing a value as $x_1 \cdot 100 + x_2$ so that products stay inside the plain modulus |
| **FHE** (Fully Homomorphic Encryption) | Encryption that allows any computation on ciphertexts without decrypting them |
| **Galois keys** | Evaluation keys that let the CS rotate the slots of a ciphertext |
| **HE** (Homomorphic Encryption) | Encryption that supports some operations on ciphertexts |
| **HM** (Harmonic Mean) | The count of values divided by the sum of their reciprocals. Always ≤ AM for positive values |
| **LUT** (Look-Up Table) | A pair of encrypted tables, input values and their outputs, used to evaluate a function BFV cannot compute directly |
| **LUT provider** | The party that builds the encrypted lookup tables ahead of time |
| **Multiplicative depth** | The longest chain of ciphertext multiplications in a computation; it determines the noise budget needed |
| **Noise budget** | How much more noise a ciphertext can take before it no longer decrypts correctly |
| **PIR** (Private Information Retrieval) | Retrieving an entry from a database without revealing which entry |
| **Plain modulus** | The modulus of the integers BFV encrypts; here 786433. Every encoded value must stay below it |
| **Plaintext** | Unencrypted, encoded data |
| **$Q_d$** | The daily HM/AM ratio for day $d$, the analytic the system computes |
| **Relinearization keys** | Evaluation keys that shrink a ciphertext back to its normal size after a multiplication |
| **SEAL** | Microsoft's homomorphic encryption library; version 4.1.2 is used here |
| **Secure Multiparty Computation** | Several parties jointly computing a function without revealing their inputs to each other |
| **TA** (Trusted Authority) | The party that holds the secret key, finds table indices and builds PIR queries. The report calls it the utility provider or water center |

## References

As listed in the project report:

1. Smart Grid Detection Simulation
2. IEEE Privacy Preserving Analytics Publication
3. Professor Shameek PPA Paper
4. Professor Shameek Forensics Paper
5. Detection of False Data Injection in Smart Water Metering Infrastructure

The report doesn't give full citations for these.
