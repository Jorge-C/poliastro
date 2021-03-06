"""Two-body dynamics.

"""

import numpy as np

from .util import transform
from . import _ast2body

__all__ = ['hohmann', 'coe2rv', 'rv2coe', 'kepler']


def hohmann(k, r_i, r_f):
    """Performs Hohmann transfer between two circular orbits.

    """
    a_trans = (r_i + r_f) / 2
    vi = np.sqrt(k / r_i)
    va = np.sqrt(2 * (k / r_i - k / (2 * a_trans)))
    dva = va - vi
    vb = np.sqrt(2 * (k / r_f - k / (2 * a_trans)))
    vf = np.sqrt(k / r_f)
    dvb = vf - vb
    t_trans = np.pi * np.sqrt(a_trans ** 3 / k)
    return dva, dvb, a_trans, t_trans


def bielliptic(k, r_i, r_b, r_f):
    """Performs bielliptic transfer between two circular orbits.

    """
    a_trans1 = (r_i + r_b) / 2
    a_trans2 = (r_b + r_f) / 2
    vi = np.sqrt(k / r_i)
    va1 = np.sqrt(2 * (k / r_i - k / (2 * a_trans1)))
    dva = va1 - vi
    vb1 = np.sqrt(2 * (k / r_b - k / (2 * a_trans1)))
    vb2 = np.sqrt(2 * (k / r_b - k / (2 * a_trans2)))
    dvb = vb2 - vb1
    vc2 = np.sqrt(2 * (k / r_f - k / (2 * a_trans2)))
    vf = np.sqrt(k / r_f)
    dvc = vf - vc2
    t_trans1 = np.pi * np.sqrt(a_trans1 ** 3 / k)
    t_trans2 = np.pi * np.sqrt(a_trans2 ** 3 / k)
    return dva, dvb, dvc, a_trans1, a_trans2, t_trans1, t_trans2


def coe2rv(k, a, ecc, inc, omega, argp, nu, tol=1e-5):
    """Converts classical orbital elements to r, v IJK vectors.

    Parameters
    ----------
    k : float
        Standard gravitational parameter (km^3 / s^2).
    a : float
        Semi-major axis (km).
    ecc : float
        Eccentricity.
    inc : float
        Inclination (rad).
    omega : float
        Longitude of ascending node (rad).
    argp : float
        Argument of perigee (rad).
    nu : float
        True anomaly (rad).
    tol : float
        Tolerance of the algorithm to detect edge cases, default to 1e-4.

    Examples
    --------
    From Vallado 2007, ex. 2-6
    >>> p = 11067.790
    >>> ecc = 0.83285
    >>> a = p / (1 - ecc ** 2)
    >>> coe2rv(3.986e5, a, 0.83285, np.radians(87.87),
    ... np.radians(227.89), np.radians(53.38), np.radians(92.335))
    (array([ 6525.36812099,  6861.5318349 ,  6449.11861416]),
    array([ 4.90227593,  5.5331365 , -1.975709  ]))

    """
    ## Check special cases
    #truelon = omega + argp + nu
    #arglat = argp + nu
    #lonper = omega + argp

    #eq = (np.abs(inc) < tol) | (np.abs(inc - np.pi) < tol)
    #ellip_eq = (ecc > tol) & eq
    #circ_eq = (ecc < tol) & eq
    #circ_inc = (ecc < tol) & ~eq

    #nu[circ_eq] = truelon[circ_eq]
    #omega[circ_eq] = argp[circ_eq] = 0.0

    #nu[circ_inc] = arglat[circ_inc]
    #argp[circ_inc] = 0.0

    #argp[ellip_eq] = lonper[ellip_eq]
    #omega[ellip_eq] = 0.0

    # Start computing
    p = a * (1 - ecc ** 2)
    r_pqw = np.zeros(3)
    r_pqw[0] = p * np.cos(nu) / (1 + ecc * np.cos(nu))
    r_pqw[1] = p * np.sin(nu) / (1 + ecc * np.cos(nu))

    v_pqw = np.zeros(3)
    v_pqw[0] = -np.sqrt(k / p) * np.sin(nu)
    v_pqw[1] = np.sqrt(k / p) * (ecc + np.cos(nu))

    r_ijk = transform(r_pqw, 3, -argp)
    r_ijk = transform(r_ijk, 1, -inc)
    r_ijk = transform(r_ijk, 3, -omega)

    v_ijk = transform(v_pqw, 3, -argp)
    v_ijk = transform(v_ijk, 1, -inc)
    v_ijk = transform(v_ijk, 3, -omega)

    return r_ijk.T, v_ijk.T


def rv2coe(k, r, v):
    """Converts r, v to classical orbital elements.

    This is a wrapper around rv2coe from ast2body.for.

    Parameters
    ----------
    k : float
        Standard gravitational parameter (km^3 / s^2).
    r : array
        Position vector (km).
    v : array
        Velocity vector (km / s).

    Examples
    --------
    Vallado 2001, example 2-5
    >>> r = [6524.834, 6862.875, 6448.296]
    >>> v = [4.901327, 5.533756, -1.976341]
    >>> k = 3.986e5
    >>> rv2coe(k, r, v)
    (36127.55012131963, 0.83285427644495158, 1.5336055626394494,
    3.9775750028016947, 0.93174413995595795, 1.6115511711293014)

    """
    # TODO: Extend for additional arguments arglat, truelon, lonper
    r = np.asanyarray(r).astype(np.float)
    v = np.asanyarray(v).astype(np.float)
    _, a, ecc, inc, omega, argp, nu, _, _, _, _ = _ast2body.rv2coe(r, v, k)
    coe = np.vstack((a, ecc, inc, omega, argp, nu))
    if coe.shape[-1] == 1:
        coe = coe[:, 0]
    return coe


def kepler(k, r0, v0, tof):
    """Propagates orbit.

    This is a wrapper around kepler from ast2body.for.

    Parameters
    ----------
    k : float
        Gravitational constant of main attractor (km^3 / s^2).
    r0 : array
        Initial position (km).
    v0 : array
        Initial velocity (km).
    tof : float
        Time of flight (s).

    Raises
    ------
    RuntimeError
        If the status of the subroutine is not 'ok'.

    """
    r0 = np.asanyarray(r0).astype(np.float)
    v0 = np.asanyarray(v0).astype(np.float)
    tof = float(tof)
    assert r0.shape == (3,)
    assert v0.shape == (3,)
    r, v, error = _ast2body.kepler(r0, v0, tof, k)
    error = error.strip().decode('ascii')
    if error != 'ok':
        raise RuntimeError("There was an error: {}".format(error))
    return r, v
