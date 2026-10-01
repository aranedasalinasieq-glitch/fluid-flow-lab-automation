import math
from src.core import darcy_factor, reynolds, air_density, speed_of_sound, pct_error

def test_laminar():
    assert abs(darcy_factor(1000,0)-0.064)<1e-12

def test_turbulent_reasonable():
    f=darcy_factor(7.26e4,0.0012)
    assert 0.015 < f < 0.04

def test_air():
    rho=air_density(101325,293.15,0.02897,8.314462618)
    assert 1.15 < rho < 1.25
    a=speed_of_sound(1.4,287.05,293.15)
    assert 340 < a < 345

def test_error():
    assert abs(pct_error(61.6,36.4)-69.230769)<1e-5
