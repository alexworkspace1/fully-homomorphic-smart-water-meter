# SmartWaterMeter

SmartWaterMeter is an implementation of an Advanced Metering Infrastructure. This aims to provide proper monitoring and controlling water consumption in contemporary smart water systems.

### Introduction

#### Core Concepts

Communities depend on water delivery systems as essential infrastructure because they guarantee the availability of clean water for many uses, including drinking, sanitation, and industrial use. Like its electrical counterparts, Advanced Metering Infrastructure (AMI) is essential to properly monitoring and controlling water consumption in contemporary smart water systems. The Internet of Things (IoT) is used in these smart water grids, which include data management systems, communication networks, and smart meters deployed at each customer's location.

Smart water networks are vulnerable to data integrity threats, which jeopardize the precision and dependability of usage data, just like electrical grids. Both utilities and customers are seriously at risk from these kinds of attacks. Similar to deductive assaults in electrical systems, data falsification in smart water grids frequently takes the form of water theft, when reported consumption figures are lower than the real usage. Additive attacks, on the other hand, entail manipulating reported consumption figures, which may result in increased expenses and improper use of resources. Additionally, more subtle threats come in the form of camouflage attacks, which combine additive and deductive attacks to maintain the mean consumption while secretly changing individual consumption records.

#### Data Integrity

Ensuring the integrity, dependability, and effectiveness of smart water grids requires safeguarding user data while performing necessary computations for system analytics. Conventional systems often require access to individual consumption information, which raises privacy concerns and may breach privacy laws or damage customer confidence. Fully Homomorphic Encryption offers a solution by enabling secure computations on encrypted data, ensuring privacy is preserved without compromising analytical functionality.

#### Development Approach

Driven by the necessity to balance privacy concerns with computational requirements, researchers have investigated a range of privacy-preserving methods for analytics in smart water grids. While approaches like Secure Multiparty Computation and Differential Privacy provide theoretical guarantees of privacy, they often face scalability or accuracy challenges. Fully Homomorphic Encryption, in particular, offers a robust solution by enabling calculations to be performed directly on encrypted data without requiring decryption, ensuring both privacy and accuracy in data analytics.

Using a Look-Up Table (LUT) based FHE approach combined with Private Information Retrieval (PIR), we provide a privacy-preserving system inspired by the privacy-preserving system in smart energy grids designed for smart water grids in this research. By employing LUTs and PIR, our method addresses the key challenges of integrating FHE into smart water grids, providing an accurate solution that maintains user confidentiality. Early findings suggest that this innovative approach can enhance the integrity, dependability, and effectiveness of smart water grids. The following sections will detail the technology behind our method, explore implementation challenges, and present evidence of its impact on improving water management systems.

### How It Works

Each smart meter encrypts its hourly reading with the BFV scheme (Microsoft SEAL). A Computation Server (CS) aggregates the ciphertexts and computes the daily ratio of the Harmonic Mean to the Arithmetic Mean, `Q_d = Σ HM_t / Σ AM_t`, without ever decrypting a reading. The steps BFV cannot do directly (division, reciprocals, rescaling) use encrypted lookup tables. A Trusted Authority (TA), the only party holding the secret key, locates the right table entry and returns an encrypted PIR query, so the server never learns which entry was used. The encrypted result is compared against a plaintext reference to measure accuracy.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full protocol, the math, and the encoding and precision details.

### Documentation

| Document | Contents |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Parties, protocol, LUT + PIR mechanics, encoding and FHE parameters |
| [Building](docs/BUILD.md) | Installing SEAL and OpenMP, configuring CMake on macOS / Linux / WSL2, troubleshooting |
| [Usage](docs/USAGE.md) | Folder setup, input data format, running the 24-hour and 1-hour pipelines |
| [Program Reference](docs/PROGRAMS.md) | Arguments, inputs and outputs of every executable |
| [Lookup Tables](docs/LOOKUP_TABLES.md) | Table format, ranges, precision variants, keeping sizes in sync |
| [Known Issues](docs/KNOWN_ISSUES.md) | Open bugs and improvement areas from the latest code review |

The project report, test report and test plan are in the repository root as PDFs (`Senior Design Project.pdf`, `Senior Design Test Report.pdf`, `Smart Water Testing Document.pdf`).

### Repository Layout

```
.
├── README.md
├── docs/                    Project documentation
├── src/
│   ├── 24hour/              Pipeline that processes a full day per step
│   │   ├── KeyGen.cpp           Generate BFV parameters and keys
│   │   ├── MakeEncTab_1..3.cpp  Generate encrypted lookup tables (3 precision levels)
│   │   ├── Step1_CS1 … Step7_CS4.cpp   Protocol steps (CS = Computation Server, TA = Trusted Authority)
│   │   ├── CheckRes.cpp         Decrypt and save the final ratio
│   │   ├── SGSimulation.hpp     Constants and includes
│   │   ├── Utility.hpp          Helper functions
│   │   └── script.py            Runs the pipeline for every day of 2014
│   └── 1hour/               Same protocol, run hour by hour
└── *.pdf                    Project report, test report and test plan
```

### Getting Started

Clone the repository and make sure the required software below is installed:

```bash
git clone https://github.com/alexworkspace1/fully-homomorphic-smart-water-meter.git
cd fully-homomorphic-smart-water-meter/src/24hour
```

When building manually, you might run into an issue of CMake not identifying the software installed on your computer. In that case, open `CMakeLists.txt` in the variant folder (`src/24hour` or `src/1hour`). Under the comment `# Import OpenMP`, set the install paths of the required software, and make sure you correct every path. Also delete the committed `CMakeCache.txt` before configuring. [docs/BUILD.md](docs/BUILD.md) has step-by-step instructions for each platform.

Quick start (24-hour variant, after editing `CMakeLists.txt`):

```bash
rm -f CMakeCache.txt Makefile cmake_install.cmake
cmake . && make -j
mkdir -p Key Table Result ptxt_res ctxt_res
./bin/KeyGen
./bin/MakeEncTab_1
# then Steps 1–7 and CheckRes for each day — see docs/USAGE.md
```

The water usage dataset is not included in this repository. See [docs/USAGE.md](docs/USAGE.md#input-data) for the expected format.

### Requirements
- Microsoft SEAL 4.1.2 (exact version, built as a shared library)
- OpenMP 18.1.8 (the version used in development; see [docs/BUILD.md](docs/BUILD.md))
- CMake 3.10 (minimum version)
- A C++17 compiler (GCC 9.3+ or Clang) on macOS or Linux (use WSL2 on Windows)
- 8 GB RAM or more

### Optional Dependencies
For testing Microsoft SEAL yourself, you may use these optional dependencies:
- GoogleTest 1.12.1
- GoogleBenchmark 1.7.1

### Project Status

This is a research prototype from a senior design project. Some steps have known bugs, and the 1-hour pipeline does not complete in its current state. See [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) before relying on any results.

### Authors
Ben Antonellis, Alex Nguyen, Gabe Smith

### Sponsors
- Western Michigan University
- Dr. Shameek Bhattacharjee

### Faculty Advisors
- Halil Dursunoglu
- Dr. Wuwei Shen
