import unittest
from reboundp import ReboundParallel
import rebound
import numpy as np
import threading, time

MAXT = 1e5

def setup_sim(port, _):
    # set up Solar System simulation
    sim = rebound.Simulation()
    sim.add("Solar System")
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.
    
    # enable server
    sim.start_server(port=port)

    # integrate for MAXT years
    # save particle's position
    sim.integrate(MAXT)
    xyz = sim.particles[1].xyz 

    return sim, xyz

class TestPorts(unittest.TestCase):
    def test_open_ports(self):
        # test validation of run jobs
        ncores = 5
        rebp = ReboundParallel(simfunc = setup_sim, cores=ncores, 
                          port_buffer=1,
                          progressbar=False)
        jobs = np.arange(0, ncores, 1)

        # record opened ports after 1 second, then stop all sims
        open_ports = []
        threading.Timer(1, 
                lambda: [open_ports.append(rebp.current_open_ports()), 
                         rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that open ports are found
        open_ports = open_ports[0]
        self.assertEqual(len(open_ports), ncores)

    def test_fetch_sim(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6200,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # fetch sim after 1 second, then stop all sims
        sim = []
        threading.Timer(1, lambda: [sim.append(rebp.fetch_sim(6201)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that fetched sim is valid
        self.assertEqual(sim[0]._status, -1)
        self.assertEqual(len(sim[0].particles), 9)
        self.assertEqual(sim[0].integrator, "whfast")
        self.assertAlmostEqual(sim[0].dt, sim[0].particles[1].P / 20., 3)

    def test_pause_one_port(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6300,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # pause simulation after 1 second, fetch sim, then stop all sims
        sim = []
        threading.Timer(1, lambda: [rebp.pause_sim(6301), 
                                    sim.append(rebp.fetch_sim(6301)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that sim was paused
        self.assertEqual(sim[0]._status, -3)

    def test_send_space(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6310,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # pause simulation after 1 second, fetch sim, then stop all sims
        sim = []
        threading.Timer(1, lambda: [rebp.send_space(6311), 
                                    sim.append(rebp.fetch_sim(6311)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that sim was paused
        self.assertEqual(sim[0]._status, -3)

    def test_pause_all(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=2, 
                          port_buffer=1, port0=6400,
                          progressbar=False)
        jobs = np.arange(0, 2, 1)

        # pause all sims after 1 second, fetch sim, then stop all sims
        sim = []
        threading.Timer(1, lambda: [rebp.pause_all(), 
                                    sim.append(rebp.fetch_sim(6401)),
                                    sim.append(rebp.fetch_sim(6402)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that sim was paused
        self.assertEqual(sim[0]._status, -3)
        self.assertEqual(sim[1]._status, -3)

    def test_start_one(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6500,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # pause simulation after 1 second, start sim again, fetch sim, then stop all sims
        sim = []
        threading.Timer(1, lambda: [rebp.pause_sim(6501), 
                                    rebp.start_sim(6501), 
                                    sim.append(rebp.fetch_sim(6501)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that sim was paused
        self.assertEqual(sim[0]._status, -1)

    def test_start_all(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=2, 
                          port_buffer=1, port0=6600,
                          progressbar=False)
        jobs = np.arange(0, 2, 1)

        # pause all sims after 1 second, start sims again, fetch sim, then stop all sims
        sim = []
        threading.Timer(1, lambda: [rebp.pause_all(), 
                                    rebp.start_all(), 
                                    sim.append(rebp.fetch_sim(6601)),
                                    sim.append(rebp.fetch_sim(6602)),
                                    rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        rebp.run()

        # check that sim was paused
        self.assertEqual(sim[0]._status, -1)
        self.assertEqual(sim[1]._status, -1)

    def test_end_one(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6700,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # stop sim after 0.5 second
        threading.Timer(0.5, lambda: [rebp.end_sim(6701)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        result = rebp.run()
        sim = result[0][0]

        # check that sim ended early
        self.assertTrue(sim.t < MAXT)
    
    def test_send_q(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=1, 
                          port_buffer=1, port0=6710,
                          progressbar=False)
        jobs = np.arange(0, 1, 1)

        # stop sim after 0.5 second
        threading.Timer(0.5, lambda: [rebp.send_q(6711)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        result = rebp.run()
        sim = result[0][0]

        # check that sim ended early
        self.assertTrue(sim.t < MAXT)

    def test_end_current(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=2, 
                          port_buffer=2,
                          progressbar=False)
        jobs = np.arange(0, 4, 1)

        # stop all current sims (only 2) after 0.5 second
        threading.Timer(0.5, lambda: [rebp.end_all_current_sims()]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        result = rebp.run()


        # check that current sims sim ended early
        sim1 = result[0][0]
        sim2 = result[1][0]
        self.assertTrue(sim1.t < MAXT)
        self.assertTrue(sim2.t < MAXT)

        # check that other sims ended normally
        sim3 = result[2][0]
        sim4 = result[3][0]
        self.assertTrue(sim3.t == MAXT)
        self.assertTrue(sim4.t == MAXT)

    def test_end_all(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=2, 
                          port_buffer=2,
                          progressbar=False)
        jobs = np.arange(0, 10, 1)

        # stop all sims after 0.5 second
        threading.Timer(0.5, lambda: [rebp.end_all(batch_buffer=10)]).start()

        # run all jobs
        rebp.init_run(jobs=jobs)
        results = rebp.run()

        # check that all sims ended early
        for i in range(4):
            sim = results[i][0]
            self.assertTrue(sim.t < MAXT)


if __name__ == "__main__":
    unittest.main()