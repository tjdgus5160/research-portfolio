"""Wigner 3-j and 6-j symbols, from the Racah formulae.

Written out rather than imported so the optical-pumping calculation has no
dependency that could silently change under it, and so every coefficient in
that calculation can be traced to arithmetic in this repository.

Verified against closed-form values in the test at the bottom.
"""
from __future__ import annotations
from fractions import Fraction
from math import cos, factorial, sin, sqrt


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


def wigner_d(j, mp, m, beta: float) -> float:
    """Wigner small-d, d^j_{m'm}(beta) — the real rotation matrix about y.

    T/07 needs it to tip a pumped ground state onto the equator: a rotation is
    what turns populations into the coherences that precess. Written out rather
    than tabulated, for the same reason as everything else in this file.

        d^j_{m'm}(b) = sum_s (-1)^(m'-m+s)
                       sqrt((j+m')!(j-m')!(j+m)!(j-m)!)
                       / ((j+m-s)! s! (m'-m+s)! (j-m'-s)!)
                       * cos(b/2)^(2j+m-m'-2s) * sin(b/2)^(m'-m+2s)
    """
    j2, mp2, m2 = _int(j), _int(mp), _int(m)
    if abs(mp2) > j2 or abs(m2) > j2:
        return 0.0
    c, s_ = cos(beta / 2), sin(beta / 2)
    pref = sqrt(factorial((j2 + mp2) // 2) * factorial((j2 - mp2) // 2)
                * factorial((j2 + m2) // 2) * factorial((j2 - m2) // 2))
    tot = 0.0
    # s runs over the range where every factorial argument stays non-negative
    for k in range(max(0, (m2 - mp2) // 2), min((j2 + m2) // 2, (j2 - mp2) // 2) + 1):
        den = (factorial((j2 + m2) // 2 - k) * factorial(k)
               * factorial(k + (mp2 - m2) // 2) * factorial((j2 - mp2) // 2 - k))
        p_c = j2 + (m2 - mp2) // 2 - 2 * k          # 2j + m - m' - 2s, in halves
        p_s = (mp2 - m2) // 2 + 2 * k
        tot += ((-1) ** ((mp2 - m2) // 2 + k) * pref / den
                * c ** p_c * s_ ** p_s)
    return tot


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

    # Wigner d. Orthogonality holds at every angle; the explicit spin-1/2 and
    # spin-1 matrices are textbook; d(0) is the identity and d(pi) the reversal.
    from math import pi
    for j in (0.5, 1, 1.5, 2):
        n = _int(j)
        for b in (0.3, pi / 2, 2.1):
            for mp in range(-n, n + 1, 2):
                s_ = sum(wigner_d(j, mp / 2, m / 2, b) ** 2 for m in range(-n, n + 1, 2))
                check(f"d({j}) row m'={mp/2:+g} normalised at b={b:.2f}", s_, 1.0)
    check("d(1/2) +1/2,+1/2 at pi/2", wigner_d(0.5, 0.5, 0.5, pi / 2), sqrt(2) / 2)
    check("d(1/2) +1/2,-1/2 at pi/2", wigner_d(0.5, 0.5, -0.5, pi / 2), -sqrt(2) / 2)
    check("d(1) 0,0 at b=0.3", wigner_d(1, 0, 0, 0.3), cos(0.3))
    check("d(1) +1,-1 at b=0.3", wigner_d(1, 1, -1, 0.3), (1 - cos(0.3)) / 2)
    check("d(2) +2,+2 identity at b=0", wigner_d(2, 2, 2, 0.0), 1.0)
    check("d(2) +2,-2 reversal at b=pi", wigner_d(2, 2, -2, pi), 1.0)
    # A spin-F state fully polarised along z, tipped onto the equator, has
    # amplitudes sqrt(C(2F, F+m))/2^F. T/07 stands on this.
    for m, want in ((2, 1 / 4), (1, 2 / 4), (0, sqrt(6) / 4), (-1, 2 / 4), (-2, 1 / 4)):
        check(f"d(2) coherent-state amplitude m={m:+d}",
              abs(wigner_d(2, m, 2, pi / 2)), want)

    print()
    print("  PASS" if ok else "  FAIL")
    raise SystemExit(0 if ok else 1)
