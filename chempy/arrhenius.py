# -*- coding: utf-8 -*-
"""
Contains functions for the `Arrhenius equation
<https://en.wikipedia.org/wiki/Arrhenius_equation>`_
(:func:`arrhenius_equation`) and a convenience fitting routine
(:func:`fit_arrhenius_equation`).
"""
from __future__ import (absolute_import, division, print_function)

from ._util import get_backend
from .util.pyutil import defaultnamedtuple
from .units import default_constants, default_units


def _get_R(constants=None, units=None):
    if constants is None:
        R = 8.314472
        if units is not None:
            J = units.Joule
            K = units.Kelvin
            mol = units.mol
            R *= J/mol/K
    else:
        R = constants.molar_gas_constant
    return R


def arrhenius_equation(A, Ea, T, constants=None, units=None, backend=None):
    """
    Returns the rate coefficient according to the Arrhenius equation

    Parameters
    ----------
    A: float with unit
        frequency factor
    Ea: float with unit
        activation energy
    T: float with unit
        temperature
    constants: object (optional, default: None)
        if None:
            T assumed to be in Kelvin, Ea in J/(K mol)
        else:
            attributes accessed: molar_gas_constant
            Tip: pass quantities.constants
    units: object (optional, default: None)
        attributes accessed: Joule, Kelvin and mol
    backend: module (optional)
        module with "exp", default: numpy, math

    """
    be = get_backend(backend)
    R = _get_R(constants, units)
    try:
        RT = (R*T).rescale(Ea.dimensionality)
    except AttributeError:
        RT = R*T
    return A*be.exp(-Ea/RT)


def fit_arrhenius_equation(k, T, kerr=None, linearized=False):
    """ Curve fitting of the Arrhenius equation to data points

    Parameters
    ----------
    k : array_like
    T : float
    kerr : array_like (optional)
    linearized : bool

    """

    if len(k) != len(T):
        raise ValueError("k and T needs to be of equal length.")
    from math import exp
    import numpy as np
    rT = 1/T
    lnk = np.log(k)
    p = np.polyfit(rT, lnk, 1)
    R = _get_R(constants=None, units=None)
    Ea = -R*p[0]
    A = exp(p[1])
    if linearized:
        return A, Ea
    from scipy.optimize import curve_fit
    if kerr is None:
        weights = None
    else:
        weights = 1/kerr**2
    popt, pcov = curve_fit(arrhenius_equation, T, k, [A, Ea], weights)
    return popt, pcov


class ArrheniusParam(defaultnamedtuple('ArrheniusParam', 'A Ea ref', [None])):
    """ Kinetic data in the form of an Arrhenius parameterisation

    Parameters
    ----------
    Ea: float
        activation energy
    A: float
        preexponential prefactor (Arrhenius type eq.)
    ref: object (default: None)
        arbitrary reference (e.g. string representing citation key)

    Examples
    --------
    >>> k = ArrheniusParam(1e13, 40e3)
    >>> '%.5g' % k(298.15)
    '9.8245e+05'

    """

    def __call__(self, T, constants=None, units=None, backend=None):
        """ Evaluates the arrhenius equation for a specified state

        Parameters
        ----------
        T: float
        constants: module (optional)
        units: module (optional)
        backend: module (default: math)

        See also
        --------
        See :func:`chempy.arrhenius.arrhenius_equation`.

        """
        return arrhenius_equation(self.A, self.Ea, T, constants=constants,
                                  units=units, backend=backend)

    @staticmethod
    def _fmt(arg, precision, tex):
        if tex:
            unit_str = arg.dimensionality.latex.strip('$')
        else:
            from quantities.markup import config
            attr = 'unicode' if config.use_unicode else 'string'
            unit_str = getattr(arg.dimensionality, attr)
        return precision.format(float(arg.magnitude)) + " " + unit_str

    def format(self, precision, tex=False):
        try:
            str_A = self._fmt(self.A, precision, tex)
            str_Ea = self._fmt(self.Ea, precision, tex)
        except:
            str_A = precision.format(self.A)
            str_Ea = precision.format(self.Ea)
        return str_A, str_Ea

    def equation_as_string(self, precision, tex=False):
        if tex:
            return r"{}\exp \left(\frac{{{}}}{{RT}} \right)".format(
                *self.format(precision, tex))
        else:
            return "{}*exp({}/(R*T))".format(*self.format(precision, tex))

    def __str__(self):
        return self.equation_as_string('{0:.5g}')


class ArrheniusParamWithUnits(ArrheniusParam):
    def __call__(self, state, constants=default_constants, units=default_units,
                 exp=None):
        """ See :func:`chempy.arrhenius.arrhenius_equation`. """
        return super(ArrheniusParamWithUnits, self).__call__(
            state, constants, units, exp)
