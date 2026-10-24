# Building

### Requirements

| Software | Version | Notes |
|---|---|---|
| Microsoft SEAL | 4.1.2 (exact, `find_package(SEAL 4.1.2 EXACT REQUIRED)`) | Must be built as a **shared** library; the targets link `SEAL::seal_shared`. |
| CMake | 3.10 or newer | |
| C++ compiler | GCC 9.3+ or Clang with C++17 | |
| OpenMP | The project was developed with LLVM `libomp` 18.1.x on macOS | Any OpenMP-capable compiler works on Linux. |
| RAM | 8 GB or more | The Galois keys alone are about 26 MB, and the table-search steps hold many ciphertexts in memory. |

Optional, for testing SEAL itself: GoogleTest 1.12.1 and GoogleBenchmark 1.7.1.

Supported platforms are **macOS** and **Linux**. The sources include `<unistd.h>` and use `getpid()`, so a native MSVC build on Windows does not work; use **WSL2** (Ubuntu) on Windows.

### 1. Install Microsoft SEAL 4.1.2

```bash
git clone --branch v4.1.2 --depth 1 https://github.com/microsoft/SEAL.git
cd SEAL
cmake -S . -B build -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
sudo cmake --install build
```

If SEAL is installed to a non-standard prefix, pass `-DCMAKE_PREFIX_PATH=<prefix>` when configuring this project.

### 2. Install OpenMP

macOS (Homebrew):

```bash
brew install llvm libomp cmake
```

Ubuntu / WSL2:

```bash
sudo apt install build-essential cmake libomp-dev   # GCC ships OpenMP (libgomp) already
```

### 3. Adjust `CMakeLists.txt` for your machine

`src/1hour/CMakeLists.txt` and `src/24hour/CMakeLists.txt` currently hard-code the original developer's Homebrew paths under the `# Import OpenMP` comment:

```cmake
set(CMAKE_C_COMPILER "/opt/homebrew/Cellar/llvm/18.1.6/bin/clang")
set(CMAKE_CXX_COMPILER "/opt/homebrew/Cellar/llvm/18.1.6/bin/clang++")
set(OPENMP_LIBRARIES "/opt/homebrew/Cellar/libomp/18.1.6/lib")
set(OPENMP_INCLUDES "/opt/homebrew/Cellar/libomp/18.1.6/include")
```

- **macOS:** change the four paths to your installed versions. `brew --prefix llvm` and `brew --prefix libomp` print them.
- **Linux / WSL2:** comment out the two `CMAKE_C_COMPILER` / `CMAKE_CXX_COMPILER` lines so CMake uses the system compiler. `find_package(OpenMP REQUIRED)` then finds GCC's OpenMP automatically.

### 4. Remove the committed CMake cache

Each variant folder contains generated files (`CMakeCache.txt`, `Makefile`, `cmake_install.cmake`) from the original developer's machine. CMake refuses to configure while `CMakeCache.txt` points at a different directory, so delete these files in your local copy first:

```bash
cd src/24hour            # or src/1hour
rm -f CMakeCache.txt Makefile cmake_install.cmake
rm -rf CMakeFiles
```

### 5. Build

```bash
cmake .
make -j
```

Executables are written to `src/<variant>/bin/`. Run them from `src/<variant>` (see [USAGE.md](USAGE.md)), because every program uses paths relative to the current directory (`Key/`, `Table/`, `Result/`).

### Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Could not find a configuration file for package "SEAL" ... version 4.1.2` | SEAL is missing or a different version. Install exactly 4.1.2, or point `CMAKE_PREFIX_PATH` at it. |
| `SEAL::seal_shared` target not found | SEAL was built static. Rebuild it with `-DBUILD_SHARED_LIBS=ON`. |
| `The current CMakeCache.txt directory ... is different` | Delete the committed cache files (step 4). |
| `Could NOT find OpenMP_CXX` on macOS | `libomp` is not installed, or the paths in `CMakeLists.txt` do not match your Homebrew versions. |
| Errors that the compiler path does not exist on Linux | The Homebrew compiler lines were not commented out (step 3). |
| `error while loading shared libraries: libseal.so.4.1` | Run `sudo ldconfig` after installing SEAL, or add its `lib` folder to `LD_LIBRARY_PATH`. |
