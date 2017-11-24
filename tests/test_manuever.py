import numpy as np
from astro import maneuver, constants, kepler
import pdb
class TestRVFPA2OrbitEl():
    r = 4 * constants.earth.radius
    v = 4.54 # km /sec
    fpa = np.deg2rad(-40)
    a_true = 37477.21798
    p_true = 19751.017296
    ecc_true = 0.687739800
    nu_true = 4.377814485
    a, p, ecc, nu = maneuver.rvfpa2orbit_el(r, v, fpa, constants.earth.mu)

    def test_semimajor_axis(self):
        """AAE532 PS6
        """
        np.testing.assert_allclose(self.a, self.a_true)

    def test_semiparameter(self):
        """AAE532 PS6
        """
        np.testing.assert_allclose(self.p, self.p_true)
    
    def test_eccentricy(self):
        np.testing.assert_allclose(self.ecc, self.ecc_true)

    def test_true_anomaly(self):
        np.testing.assert_allclose(self.nu, self.nu_true)

class TestSingleImpulse():
    # 2017 HW5 Problem 1
    rm = 59029.6
    vm = 1.69
    fpam = np.deg2rad(27.45)
    delta_v = 1.2
    alpha = np.deg2rad(30)
    rf, vf, fpaf = maneuver.single_impulse(rm, vm, fpam, delta_v, alpha)

    rf_true = rm
    vf_true = 2.7944049
    fpaf_true = np.deg2rad(39.84879352)

    def test_position(self):
        np.testing.assert_allclose(self.rf, self.rf_true) 
    
    def test_velocity(self):
        np.testing.assert_allclose(self.vf, self.vf_true)

    def test_flight_path_angle(self):
        np.testing.assert_allclose(self.fpaf, self.fpaf_true)

def test_delta_v_solve_planar():
    v1 = 2.455
    v2 = 2.867
    fpa1 = np.deg2rad(26.03)
    fpa2 = 0
    deltav, alpha, beta = maneuver.delta_v_solve_planar(v1, v2, fpa1, fpa2)
    deltav_true = 1.2639818
    alpha_true = 1.47477394
    beta_true = np.pi - alpha
    np.testing.assert_allclose(deltav, deltav_true)
    np.testing.assert_allclose(alpha, alpha_true)
    np.testing.assert_allclose(beta, beta_true)

def test_planar_orbit_intersection():
    ecc1 = 0.75
    p1 = kepler.semilatus_rectum(4.5*constants.earth.radius, ecc1)
    a2, p2, ecc2 = kepler.perapo2aecc(2 * constants.earth.radius, 6 * constants.earth.radius)
    dargp = np.deg2rad(35)

    nu = maneuver.planar_conic_orbit_intersection(p1, p2, ecc1, ecc2, dargp)
    np.testing.assert_allclose(nu, np.deg2rad(110.342156))

def test_vel_mag():
    r = 5.04 * constants.earth.radius 
    a = 6 * constants.earth.radius
    mu = constants.earth.mu
    v_true = 3.79259
    v = maneuver.vel_mag(r, a, mu)
    np.testing.assert_allclose(v, v_true, rtol=1e-4)

def test_synodic_period():
    a1 = constants.earth.orbit_sma 
    a2 = constants.mars.orbit_sma 
    mu = constants.sun.mu 
    S_true = 67377144.56697
    S = maneuver.synodic_period(a1, a2, mu)
    np.testing.assert_allclose(S, S_true, rtol=1e-4)
