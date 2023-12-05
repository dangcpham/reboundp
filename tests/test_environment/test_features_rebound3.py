import unittest
import reboundp
import rebound
import numpy as np
import threading, time

def setup_sim_int():
    # set up Solar System simulation
    sim = rebound.Simulation()
    sim.add("Solar System")
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.

    # integrate for 10^2 years
    # save Jupiter's position
    t_arr = np.linspace(0, 1e2, 100)
    jupiter_xyz = np.zeros((len(t_arr), 3))
    for i, t in enumerate(t_arr):
        sim.integrate(t, exact_finish_time=0)
        if sim.t < t:
            # warnings.warn("Simulation stopped early.")
            break
        jupiter_xyz[i] = sim.particles[5].xyz 

class TestFeaturesReb3(unittest.TestCase):
    def test_checkreb3(self):
        sim = rebound.Simulation()
        with self.assertRaises(AttributeError):
            sim.start_server(port=1234)

    def test_features_reb3(self):
        rebp = reboundp.ReboundParallel(setup_sim_int)
        rebp.run(jobs=4, cores=4)

if __name__ == "__main__":
    unittest.main()