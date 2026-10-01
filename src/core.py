from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Iterable
import numpy as np

LENGTH_TO_M = {
    "m": 1.0, "cm": 1e-2, "mm": 1e-3,
    "inhg": 0.0254, "mmhg": 1e-3, "mhg": 1.0,
    "inh2o": 0.0254, "mmh2o": 1e-3,
}

def norm_unit(u):
    return str(u).strip().lower().replace("₂", "2").replace(" ", "")

def length_to_m(value, unit):
    u = norm_unit(unit)
    if u not in LENGTH_TO_M:
        raise ValueError(f"Unidad de longitud/manómetro no soportada: {unit}")
    return float(value) * LENGTH_TO_M[u]

def manometer_dp(h1, h2, unit, rho_man, rho_process, g):
    dh = abs(length_to_m(h1, unit) - length_to_m(h2, unit))
    return dh, abs(rho_man - rho_process) * g * dh

def water_manometer_dp(dh_value, unit, rho_water, rho_air, g):
    u = norm_unit(unit)
    if u == "pa":
        return abs(float(dh_value))
    h = length_to_m(dh_value, unit)
    return abs(rho_water - rho_air) * g * abs(h)

def area_circle(d):
    return math.pi * d*d / 4.0

def reynolds(rho, v, d, mu):
    return rho * abs(v) * d / mu

def flow_regime(re):
    if re < 2300:
        return "laminar"
    if re <= 4000:
        return "transición"
    return "turbulento"

def darcy_factor(re, rel_roughness, tol=1e-12, max_iter=100):
    if re <= 0:
        raise ValueError("Re debe ser positivo.")
    if re < 2300:
        return 64.0/re
    # Colebrook-White, initialized with Haaland.
    rr = max(float(rel_roughness), 0.0)
    f = (-1.8*math.log10((rr/3.7)**1.11 + 6.9/re))**-2
    for _ in range(max_iter):
        rhs = -2.0*math.log10(rr/3.7 + 2.51/(re*math.sqrt(f)))
        f_new = 1.0/(rhs*rhs)
        if abs(f_new-f) < tol:
            return f_new
        f = f_new
    return f

def pct_error(exp, ref):
    return abs((exp-ref)/ref)*100.0 if ref != 0 else math.nan

def signed_deviation(exp, ref):
    return ((exp-ref)/ref)*100.0 if ref != 0 else math.nan

@dataclass
class Calibration:
    a: float
    b: float
    r2: float
    dp_min: float
    dp_max: float

    def q(self, dp):
        if dp < 0:
            raise ValueError("ΔP no puede ser negativo.")
        return self.a*math.sqrt(dp) + self.b

def fit_orifice(dp: Iterable[float], q: Iterable[float]) -> Calibration:
    dp = np.asarray(list(dp), dtype=float)
    q = np.asarray(list(q), dtype=float)
    if len(dp) < 3:
        raise ValueError("Se requieren al menos 3 mediciones de calibración.")
    x = np.sqrt(np.clip(dp, 0, None))
    a, b = np.polyfit(x, q, 1)
    pred = a*x+b
    ss_res = float(np.sum((q-pred)**2))
    ss_tot = float(np.sum((q-np.mean(q))**2))
    r2 = 1.0 - ss_res/ss_tot if ss_tot > 0 else 1.0
    return Calibration(float(a), float(b), r2, float(dp.min()), float(dp.max()))

def air_density(p, T_K, molar_mass, Ru):
    return p*molar_mass/(Ru*T_K)

def speed_of_sound(gamma, R_air, T_K):
    return math.sqrt(gamma*R_air*T_K)

def pitot_velocity(dp, rho_air, coefficient=1.0):
    return coefficient*math.sqrt(2.0*dp/rho_air)

def trapz_mean_velocity(positions, velocities):
    x = np.asarray(positions, dtype=float)
    v = np.asarray(velocities, dtype=float)
    order = np.argsort(x)
    x, v = x[order], v[order]
    span = x[-1]-x[0]
    if span <= 0:
        return float(np.mean(v))
    return float(np.trapz(v, x)/span)
