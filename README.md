# 🔐 CIPHERLAB — Classical Cryptography Studio

**Network and Information Security (CT-486) — Complex Computing Problem (CCP)**
NED University of Engineering and Technology
Course Instructor: **Dr. Shariq Mahmood Khan**

CIPHERLAB is an educational cryptography project that combines two classical ciphers — the **Vigenère cipher** and the **2×2 Hill cipher** — into a single product cipher. It also demonstrates how this combined cipher can be broken using a **known-plaintext (known-prefix) attack**, and measures performance through a built-in benchmark.

The project comes with a modern desktop GUI (built with CustomTkinter) and a command-line version.

> ⚠️ **Disclaimer:** This is a classical-cipher learning exercise. It is **not** secure encryption and must not be used to protect real data.

---

## ✨ Features

- **Encryption** — Converts plaintext into marked ciphertext using Vigenère followed by Hill.
- **Decryption** — Recovers the cleaned plaintext using the secret key.
- **Cryptanalysis** — Known-prefix attack that recovers the plaintext, the Hill matrix and the Vigenère shifts **without the secret key**.
- **Benchmark Lab** — Compares execution time of the attack, a simple Shift (Caesar) cipher, and the custom encryption/decryption across different message lengths, with a bar chart and results table.
- **Frequency analysis** (CLI) — Compares ciphertext letter frequencies with standard English frequencies.
- **Documentation page** — In-app technical reference for the cipher design.
- **Input validation** — Strict checks on key format, matrix invertibility and ciphertext structure.

---

## 📁 Project Structure

```
NIS-CCP/
├── app.py               # CIPHERLAB desktop GUI (CustomTkinter)
├── cipher.py            # Core cipher logic, attack, benchmark + CLI menu
├── NIS CCP Report.pdf   # Full project report
└── __pycache__/         # Python cache files
```

---

## 🧠 How the Cipher Works

### Key Structure
The key is **exactly 10 uppercase letters (A–Z)**, for example `CRYPTOHILL`:

| Part | Characters | Purpose |
|------|-----------|---------|
| First 6 letters | `CRYPTO` | Vigenère key |
| Last 4 letters | `HILL` | 2×2 Hill matrix (row-major order) |

The Hill matrix must be invertible modulo 26 (its determinant must be coprime to 26), otherwise the key is rejected.

### Plaintext Cleaning
Only letters A–Z are kept. Lowercase letters are converted to uppercase, and spaces, digits and punctuation are removed. Original formatting is not recovered after decryption.

### Encryption Process
1. Clean the plaintext.
2. Apply the **Vigenère** cipher using the 6-letter key.
3. If the message length is odd, append an `X` as padding.
4. Apply the **Hill** cipher on pairs of letters.
5. Add a leading **parity marker**: `A` for even-length plaintext, `B` for odd-length plaintext.

### Decryption Process
1. Read and validate the marker.
2. Apply the **inverse Hill** matrix.
3. Remove the `X` padding if the marker is `B`.
4. Reverse the **Vigenère** cipher.

### Ciphertext Format
```
[A|B] + even-length Hill ciphertext body
```

### Example
```
Key:        CRYPTOHILL
Plaintext:  Meet me at the library at noon
Cleaned:    MEETMEATTHELIBRARYATNOON
Ciphertext: AGVAGXTQCJNXIGWRSKIQCXYFK
```

---

## 🕵️ Known-Prefix Attack

Because a 6-letter Vigenère key repeats every 3 Hill blocks, each ciphertext block can be written as:

```
C_j = H · P_j + t_(j mod 3)   (mod 26)
```

where `H` is the Hill matrix and `t` is a phase-dependent offset produced by the Vigenère shifts.

The attack works as follows:
1. Split the known prefix and ciphertext into aligned pairs, grouped by phase (0, 1, 2).
2. Subtract two blocks of the same phase to cancel the offset `t`.
3. Find two difference vectors whose determinant is invertible mod 26 and solve `H = ΔC · ΔP⁻¹`.
4. Compute the three offsets and recover equivalent Vigenère shifts.
5. Decrypt the full ciphertext and verify that it matches the known prefix.

**Requirements:** the prefix must be shorter than the message, must cover all three phases, and must give an invertible pair of differences. Complexity is **O(m² + n)** for `m` known pairs and `n` ciphertext letters.

**Example:** with only the prefix `ATTACKATDAWNTHEENEMY` and the ciphertext, the attack recovers the full message, the Hill matrix `[[7, 8], [11, 11]]` and the Vigenère key `CRYPTO`.

---

## 📊 Benchmark Lab

- Message lengths tested: **41, 80, 161, 320** letters
- Random A–Z messages and valid random keys, fixed seed **486** for reproducibility
- Trials per length: configurable (1–100, default 20)
- Attack uses the first **20** plaintext letters as the known prefix
- Every trial verifies a full encryption → decryption round trip

Results show mean time in milliseconds for the attack, Shift encryption, custom encryption and custom decryption, along with the attack success rate. Timings vary with the machine and system load.

---

## ⚙️ Installation & Usage

### Requirements
- Python **3.8+** (uses `pow(x, -1, 26)` for modular inverse)
- `customtkinter` (only for the GUI)
- Tkinter (bundled with most Python installations)

### Setup
```bash
git clone https://github.com/Fabihafaheem2004/NIS-CCP.git
cd NIS-CCP
pip install customtkinter
```

### Run the GUI
```bash
python app.py
```

**Keyboard shortcuts:** `Ctrl+H` — Home, `Ctrl+L` — Clear workspace

### Run the Command-Line Version
```bash
python cipher.py
```
```
1. Encrypt  2. Decrypt  3. Known-prefix attack  4. Benchmark  5. Exit
```

---

## 🛡️ Security Notes

This cipher is weak by design because both components are linear. A small amount of known plaintext is enough to recover the full key structure. It was built to study how classical techniques can be combined and why such combinations still fail against known-plaintext attacks. Detailed security analysis, attack results, improvement suggestions and performance metrics are available in **`NIS CCP Report.pdf`**.

---

## 👩‍💻 Contributors

| Name | Roll No. |
|------|----------|
| Fabiha Faheem | CR-23002 |
| Maryam Habib | CR-23004 |
| Hareem Khan | CR-23023 |
| Emaan Rashid | CR-23029 |
