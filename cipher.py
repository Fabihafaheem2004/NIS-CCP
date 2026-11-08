#!/usr/bin/env python3
"""Educational Vigenere + 2x2 Hill cipher and keyless known-prefix attack.

Key: exactly 10 uppercase ASCII letters, e.g. CRYPTOHILL. The first six
are the Vigenere key; the last four are the Hill matrix in row-major order.
Plaintext is cleaned: lowercase ASCII becomes uppercase, and every character
outside ASCII A-Z is discarded. Formatting is not recovered.

Ciphertext FORMAT CHANGE from the original program: exactly one leading
marker A (even cleaned plaintext length) or B (odd length), followed by an
even-length Hill ciphertext body. X padding is appended AFTER Vigenere and
is removed BEFORE inverse Vigenere. This format is not compatible with the
original markerless ciphertext unless it is converted separately.

This is a classical-cipher learning exercise, NOT secure encryption.
"""

from collections import Counter
from math import gcd
import random
import string
import time

ALPHABET = string.ascii_uppercase
# Approximate expected percentages in ordinary English prose.
ENGLISH = (8.17, 1.49, 2.78, 4.25, 12.70, 2.23, 2.02, 6.09, 6.97,
           0.15, 0.77, 4.03, 2.41, 6.75, 7.51, 1.93, 0.10, 5.99,
           6.33, 9.06, 2.76, 0.98, 2.36, 0.15, 1.97, 0.07)


def clean_plaintext(text):
    """Keep only ASCII letters and convert lowercase to uppercase."""
    return ''.join(c.upper() for c in text if 'A' <= c <= 'Z' or 'a' <= c <= 'z')


def number(letter):
    return ord(letter) - ord('A')


def letter(value):
    return chr(value % 26 + ord('A'))


def inverse_matrix(matrix):
    """Return the 2x2 matrix inverse mod 26, or raise ValueError."""
    (a, b), (c, d) = matrix
    det = (a * d - b * c) % 26
    if gcd(det, 26) != 1:
        raise ValueError('Hill matrix determinant must be coprime to 26.')
    inv_det = pow(det, -1, 26)
    return ((d * inv_det % 26, -b * inv_det % 26),
            (-c * inv_det % 26, a * inv_det % 26))


def matrix_times_vector(matrix, vector):
    (a, b), (c, d) = matrix
    x, y = vector
    return ((a*x + b*y) % 26, (c*x + d*y) % 26)


def matrix_multiply(left, right):
    return tuple(tuple(sum(left[i][k] * right[k][j] for k in range(2)) % 26
                       for j in range(2)) for i in range(2))


def parse_key(key):
    if len(key) != 10 or any(c not in ALPHABET for c in key):
        raise ValueError('Key must be exactly 10 uppercase ASCII letters A-Z.')
    h = [number(c) for c in key[6:]]
    hill = ((h[0], h[1]), (h[2], h[3]))
    inverse_matrix(hill)  # reject non-invertible matrices
    return key[:6], hill


def parse_ciphertext(ciphertext):
    """Strictly validate the new marker + body format; no silent cleaning."""
    if any(c not in ALPHABET for c in ciphertext):
        raise ValueError('Ciphertext must contain uppercase ASCII letters A-Z only.')
    if len(ciphertext) < 3:
        raise ValueError('Ciphertext needs a marker and at least one two-letter block.')
    if ciphertext[0] not in 'AB':
        raise ValueError('Marker must be A (even) or B (odd).')
    body = ciphertext[1:]
    if len(body) % 2:
        raise ValueError('The ciphertext body after the marker must have even length.')
    return ciphertext[0], body


def vigenere_encrypt(text, key):
    return ''.join(letter(number(c) + number(key[i % 6])) for i, c in enumerate(text))


def vigenere_decrypt(text, key):
    return ''.join(letter(number(c) - number(key[i % 6])) for i, c in enumerate(text))


def hill_transform(text, matrix):
    """Transform an even-length text, with matrix or its inverse."""
    if len(text) % 2:
        raise ValueError('Hill input must contain complete pairs.')
    result = []
    for i in range(0, len(text), 2):
        x, y = matrix_times_vector(matrix, (number(text[i]), number(text[i+1])))
        result.extend((letter(x), letter(y)))
    return ''.join(result)


def encrypt(plaintext, key):
    vig, hill = parse_key(key)
    plain = clean_plaintext(plaintext)
    if not plain:
        raise ValueError('Plaintext must contain at least one ASCII letter.')
    marker = 'B' if len(plain) % 2 else 'A'
    intermediate = vigenere_encrypt(plain, vig)
    if marker == 'B':
        intermediate += 'X'  # padding belongs to the Hill input, not plaintext
    return marker + hill_transform(intermediate, hill)


def decrypt(ciphertext, key):
    vig, hill = parse_key(key)
    marker, body = parse_ciphertext(ciphertext)
    intermediate = hill_transform(body, inverse_matrix(hill))
    if marker == 'B':
        if intermediate[-1] != 'X':
            raise ValueError('Invalid odd-length padding (or wrong key/ciphertext).')
        intermediate = intermediate[:-1]
    return vigenere_decrypt(intermediate, vig)


def known_plaintext_attack(known_prefix, ciphertext):
    """Recover using only a plaintext PREFIX and the complete marked ciphertext.

    For block j, C_j = H P_j + t_(j mod 3) (mod 26), where H is
    the Hill matrix and t_phase = H * the two Vigenere shifts.
    Subtract two blocks in the same phase to cancel t. Two such difference
    vectors (they can come from different phases) with unit determinant give
    H = deltaC * inverse(deltaP). Use known pairs to solve all 3 offsets.

    Full, non-padding blocks only are used as equations. With m known full
    blocks and n ciphertext letters, the search is O(m^2 + n) for fixed
    alphabet size: at most 26^2 distinct plaintext difference vectors are
    stored, each compared against at most 26^2 others. Space is O(m + n)
    plus the fixed-size difference table. Failure does not prove no other
    attack exists. Prefix must be shorter than the original message.
    """
    marker, body = parse_ciphertext(ciphertext)
    prefix = clean_plaintext(known_prefix)
    plain_length = len(body) - (marker == 'B')
    if not prefix:
        raise ValueError('The known prefix must contain at least one ASCII letter.')
    if len(prefix) >= plain_length:
        raise ValueError('The known prefix must be shorter than the message.')

    blocks = []
    groups = [[], [], []]
    # Ignore an incomplete prefix pair. The padded block is never a full
    # plaintext pair for an odd-length message, even if the prefix is long.
    for j in range(len(prefix) // 2):
        p = (number(prefix[2*j]), number(prefix[2*j+1]))
        c = (number(body[2*j]), number(body[2*j+1]))
        blocks.append((j % 3, p, c))
        groups[j % 3].append((p, c))
    if any(not group for group in groups):
        return {'success': False, 'reason': 'A phase is unobserved: need at least one complete known pair in each of the three phases.'}

    differences = {}  # delta P -> corresponding delta C, bounded by 26^2
    hill = None
    for group in groups:
        for i in range(len(group)):
            p1, c1 = group[i]
            for j in range(i):
                p0, c0 = group[j]
                dp = ((p1[0]-p0[0]) % 26, (p1[1]-p0[1]) % 26)
                dc = ((c1[0]-c0[0]) % 26, (c1[1]-c0[1]) % 26)
                if dp in differences:
                    # Inconsistency is evidence that the prefix/ciphertext do
                    # not satisfy the assumed model, even if no basis is found.
                    if differences[dp] != dc:
                        return {'success': False, 'reason': 'Known pairs are inconsistent with the cipher model.'}
                    continue
                for old_dp, old_dc in differences.items():
                    delta_p = ((old_dp[0], dp[0]), (old_dp[1], dp[1]))
                    if gcd(old_dp[0]*dp[1] - dp[0]*old_dp[1], 26) == 1:
                        delta_c = ((old_dc[0], dc[0]), (old_dc[1], dc[1]))
                        hill = matrix_multiply(delta_c, inverse_matrix(delta_p))
                        break
                if hill is not None:
                    break
                differences[dp] = dc
            if hill is not None:
                break
        if hill is not None:
            break
    if hill is None:
        return {'success': False, 'reason': 'No two same-phase difference vectors have an invertible determinant mod 26. Try a longer or more varied prefix.'}
    try:
        inverse_hill = inverse_matrix(hill)
    except ValueError:
        return {'success': False, 'reason': 'Recovered Hill matrix is not invertible; inputs are inconsistent.'}

    offsets = []
    for group in groups:
        p, c = group[0]
        hp = matrix_times_vector(hill, p)
        offsets.append(((c[0]-hp[0]) % 26, (c[1]-hp[1]) % 26))
    # A candidate must explain EVERY complete known pair, not just the basis.
    for phase, p, c in blocks:
        hp = matrix_times_vector(hill, p)
        predicted = ((hp[0]+offsets[phase][0]) % 26,
                     (hp[1]+offsets[phase][1]) % 26)
        if predicted != c:
            return {'success': False, 'reason': 'Recovered candidate is inconsistent with the known plaintext pairs.'}

    # Recover equivalent Vigenere shifts from t = H*k, then reverse stages.
    shifts = [matrix_times_vector(inverse_hill, t) for t in offsets]
    vig = ''.join(letter(x) for pair in shifts for x in pair)
    intermediate = hill_transform(body, inverse_hill)
    if marker == 'B':
        if intermediate[-1] != 'X':
            return {'success': False, 'reason': 'Recovered candidate has invalid odd-length Hill padding.'}
        intermediate = intermediate[:-1]
    recovered = vigenere_decrypt(intermediate, vig)
    # Also checks a trailing unpaired known character.
    if not recovered.startswith(prefix):
        return {'success': False, 'reason': 'Recovered candidate does not match the entire supplied prefix.'}
    return {'success': True, 'plaintext': recovered, 'hill_matrix': hill,
            'vigenere_key': vig, 'offsets': offsets}


def frequency_comparison(ciphertext):
    """Print descriptive letter frequencies, excluding the parity marker."""
    _, body = parse_ciphertext(ciphertext)
    counts = Counter(body)
    print('\nLetter  Ciphertext %  Approx. English %')
    for i, c in enumerate(ALPHABET):
        print(f'  {c}       {counts[c] / len(body) * 100:6.2f}          {ENGLISH[i]:6.2f}')
    print('These frequencies are descriptive, not a break or proof of security.')
    print('Short texts and non-English/uniform random texts can differ greatly from English.')


def random_key(rng):
    """Generate a valid key for reproducible experiments, not for security."""
    while True:
        key = ''.join(rng.choice(ALPHABET) for _ in range(10))
        try:
            parse_key(key)
            return key
        except ValueError:
            pass


def shift_encrypt(text, shift=3):
    return ''.join(letter(number(c) + shift) for c in text)


def benchmark(trials=20, seed=486):
    """Time real trials. Success means the entire recovered text equals truth."""
    rng = random.Random(seed)
    print('\nEXPERIMENT: reproducible uniform random A-Z text and valid random keys')
    print(f'Seed: {seed}; trials per length: {trials}; known prefix: first 20 letters.')
    print('Lengths below are plaintext lengths; ciphertext has a marker and possible pad.')
    print('Times are mean wall-clock milliseconds per trial, including failures.')
    print('  Plain   Cipher  Success   Attack ms   Shift enc ms   Custom enc ms   Custom dec ms')
    for length in (41, 80, 161, 320):
        successes = 0
        totals = [0.0, 0.0, 0.0, 0.0]
        ct_len = 0
        for _ in range(trials):
            message = ''.join(rng.choice(ALPHABET) for _ in range(length))
            key = random_key(rng)
            start = time.perf_counter()
            shift_encrypt(message)
            totals[1] += time.perf_counter() - start
            start = time.perf_counter()
            ciphertext = encrypt(message, key)
            totals[2] += time.perf_counter() - start
            start = time.perf_counter()
            roundtrip = decrypt(ciphertext, key)
            totals[3] += time.perf_counter() - start
            if roundtrip != message:
                raise RuntimeError('Encryption/decryption round trip failed.')
            start = time.perf_counter()
            result = known_plaintext_attack(message[:20], ciphertext)
            totals[0] += time.perf_counter() - start
            successes += int(result['success'] and result['plaintext'] == message)
            ct_len = len(ciphertext)
        ms = [x * 1000 / trials for x in totals]
        print(f'{length:7d} {ct_len:8d}  {successes:2d}/{trials:<2d} '
              f'{100*successes/trials:5.1f}%  {ms[0]:9.4f}   {ms[1]:12.4f}'
              f'   {ms[2]:13.4f}   {ms[3]:13.4f}')
    print('\nTimes depend on machine, system load and Python; fixed-seed data is reproducible, timings are not.')
    print('Timing compares these Python implementations; custom encryption includes validation and both stages.')
    print('Encryption, decryption and Shift are O(n); attack is O(m^2 + n) for m known pairs, fixed alphabet.')
    print('These random-text trials do not predict success on natural English or other datasets.')


def main():
    print('VIGENERE + HILL: educational demonstration, not secure encryption.')
    print('FORMAT CHANGE: ciphertext starts with A (even) or B (odd), unlike the original.')
    print('Plaintext is cleaned to ASCII A-Z; spaces, punctuation and formatting are lost.')
    while True:
        print('\n1. Encrypt  2. Decrypt  3. Known-prefix attack  4. Benchmark  5. Exit')
        try:
            choice = input('Choose 1-5: ').strip()
            if choice == '1':
                key = input('10-letter uppercase key (example CRYPTOHILL): ').strip()
                plaintext = input('Plaintext: ')
                print('Cleaned plaintext:', clean_plaintext(plaintext))
                print('Ciphertext:', encrypt(plaintext, key))
            elif choice == '2':
                key = input('10-letter uppercase key: ').strip()
                ciphertext = input('Marked uppercase ciphertext: ').strip()
                print('Recovered cleaned plaintext:', decrypt(ciphertext, key))
            elif choice == '3':
                ciphertext = input('Full marked uppercase ciphertext: ').strip()
                prefix = input('Known plaintext PREFIX (not the whole message): ')
                print('\nThe attacker uses only this prefix and the ciphertext, not the secret key.')
                frequency_comparison(ciphertext)
                result = known_plaintext_attack(prefix, ciphertext)
                if result['success']:
                    print('\nRecovered plaintext:', result['plaintext'])
                    print('Recovered Hill matrix:', result['hill_matrix'])
                    print('Recovered Vigenere shifts as letters:', result['vigenere_key'])
                    print('Candidate matches all known letters; unknown text cannot be independently verified without ground truth.')
                else:
                    print('\nAttack could not recover the message:', result['reason'])
                print('Requires the correct aligned prefix, all three phases, and an invertible pair of differences;')
                print('this particular method can fail even when other cryptanalysis may succeed.')
            elif choice == '4':
                benchmark()
            elif choice == '5':
                print('Goodbye.')
                break
            else:
                print('Please choose a number from 1 to 5.')
        except ValueError as exc:
            print('Input error:', exc)
        except (EOFError, KeyboardInterrupt):
            print('\nGoodbye.')
            break


if __name__ == '__main__':
    main()
