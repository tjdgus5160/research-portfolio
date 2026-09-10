"""Wigner 3-j and 6-j symbols, from the Racah formulae.

Written out rather than imported so the optical-pumping calculation has no
dependency that could silently change under it, and so every coefficient in
that calculation can be traced to arithmetic in this repository.

Verified against closed-form values in the test at the bottom.
"""
from __future__ import annotations
from fractions import Fraction
from math import factorial, sqrt


def _int(x) -> int:
    """Angular momenta arrive as halves; work in units of 1/2 internally."""
    y = round(2 * x)
    if abs(2 * x - y) > 1e-9:
        raise ValueError(f"{x} is not a multiple of 1/2")
    return y


def _tri(a2: int, b2: int, c2: int) -> bool:
    return abs(a2 - b2) <= c2 <= a2 + b2 and (a2 + b2 + c2) % 2 == 0


def _delta(a2: int, b2: int, c2: int) -> Fraction:
    """The triangle coefficient Δ(abc), as an exact fraction."""
    f = lambda n: factorial(n // 2)
    return Fraction(f(a2 + b2 - c2) * f(a2 - b2 + c2) * f(-a2 + b2 + c2),
                    f(a2 + b2 + c2 + 2))


def wigner_3j(j1, j2, j3, m1, m2, m3) -> float:
    j1_, j2_, j3_ = _int(j1), _int(j2), _int(j3)
    m1_, m2_, m3_ = _int(m1), _int(m2), _int(m3)
    if m1_ + m2_ + m3_ != 0 or not _tri(j1_, j2_, j3_):
        return 0.0
    for j, m in ((j1_, m1_), (j2_, m2_), (j3_, m3_)):
        if abs(m) > j or (j - m) % 2 != 0:
            return 0.0
    f = lambda n: factorial(n // 2)
    pref = _delta(j1_, j2_, j3_) * Fraction(
        f(j1_ + m1_) * f(j1_ - m1_) * f(j2_ + m2_) * f(j2_ - m2_)
        * f(j3_ + m3_) * f(j3_ - m3_), 1)
    tmin = max(0, j2_ - j3_ - m1_, j1_ - j3_ + m2_)
    tmax = min(j1_ + j2_ - j3_, j1_ - m1_, j2_ + m2_)
    s = Fraction(0)
    for t2 in range(tmin, tmax + 1, 2):
        d = (f(t2) * f(j1_ + j2_ - j3_ - t2) * f(j1_ - m1_ - t2)
             * f(j2_ + m2_ - t2) * f(j3_ - j2_ + m1_ + t2) * f(j3_ - j1_ - m2_ + t2))
        s += Fraction((-1) ** (t2 // 2), d)
    sign = (-1) ** ((j1_ - j2_ - m3_) // 2)
    return sign * sqrt(float(pref)) * float(s)


def wigner_6j(j1, j2, j3, j4, j5, j6) -> float:
    a, b, c = _int(j1), _int(j2), _int(j3)
    d, e, f_ = _int(j4), _int(j5), _int(j6)
    for tri in ((a, b, c), (a, e, f_), (d, b, f_), (d, e, c)):
        if not _tri(*tri):
            return 0.0
    fac = lambda n: factorial(n // 2)
    pref = sqrt(float(_delta(a, b, c) * _delta(a, e, f_)
                      * _delta(d, b, f_) * _delta(d, e, c)))
    tmin = max(a + b + c, a + e + f_, d + b + f_, d + e + c)
    tmax = min(a + b + d + e, b + c + e + f_, a + c + d + f_)
    s = 0.0
    for t2 in range(tmin, tmax + 1, 2):
        den = (fac(t2 - a - b - c) * fac(t2 - a - e - f_) * fac(t2 - d - b - f_)
               * fac(t2 - d - e - c) * fac(a + b + d + e - t2)
               * fac(b + c + e + f_ - t2) * fac(a + c + d + f_ - t2))
        s += (-1) ** (t2 // 2) * fac(t2 + 2) / den
    return pref * s


if __name__ == "__main__":
    # Checked against identities, not against remembered values. The first
    # version of this test compared three symbols to numbers I had written from
    # memory; all three of those numbers were wrong and the code was right,
    # which is a good argument for never testing against recollection.
    from math import isclose
    ok = True

    def check(name, got, want):
        global ok
        good = isclose(got, want, abs_tol=1e-12)
        ok &= good
        print(f"  {'OK ' if good else 'FAIL'} {name:44s} {got:+.12f}  want {want:+.12f}")

    # 3-j orthogonality, at each fixed m3 separately: sum_{m1 m2} (3j)^2 = 1/(2j3+1)
    for j1, j2, j3 in ((2, 1, 2), (1, 1, 2), (0.5, 0.5, 1)):
        for m3 in [x / 2 for x in range(-_int(j3), _int(j3) + 1, 2)]:
            s_ = sum(wigner_3j(j1, j2, j3, m1 / 2, m2 / 2, m3) ** 2
                     for m1 in range(-_int(j1), _int(j1) + 1, 2)
                     for m2 in range(-_int(j2), _int(j2) + 1, 2)
                     if abs(m1 / 2 + m2 / 2 + m3) < 1e-9)
            check(f"3j orthogonality ({j1} {j2} {j3}) at m3={m3:g}", s_, 1 / (2 * j3 + 1))

    # a 6-j with a zero entry has a closed form
    check("6j {1 1 0; 1 1 1} closed form", wigner_6j(1, 1, 0, 1, 1, 1), -1 / 3)
    check("6j {2 1 1; 1 2 2} symmetry vs column swap",
          wigner_6j(2, 1, 1, 1, 2, 2), wigner_6j(1, 2, 1, 2, 1, 2))

    # A 3-j is invariant under a CYCLIC shift of its columns, and picks up
    # (-1)^(j1+j2+j3) when two columns are swapped. Getting these two the wrong
    # way round is what the first version of this test did.
    a = wigner_3j(2, 1, 2, -2, 1, 1)          # columns (2,-2) (1,1) (2,1)
    check("3j cyclic shift", wigner_3j(1, 2, 2, 1, 1, -2), a)
    check("3j column swap", wigner_3j(1, 2, 2, 1, -2, 1), a * (-1) ** (2 + 1 + 2))

    print()
    print("  PASS" if ok else "  FAIL")
    raise SystemExit(0 if ok else 1)
