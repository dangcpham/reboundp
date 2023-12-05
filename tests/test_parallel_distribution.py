import unittest
from reboundp import ReboundParallel
import rebound
import numpy as np

def setup_sim(port, sim_id):
    # set up Solar System simulation
    sim = rebound.Simulation()
    sim.add("Solar System")
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.

    # enable server
    sim.start_server(port=port)

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

    return sim, sim_id, t_arr, jupiter_xyz

def setup_sim_noport(sim_id):
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

    return sim, sim_id, t_arr, jupiter_xyz

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

    return sim, t_arr, jupiter_xyz

class TestInitialization(unittest.TestCase):
    def test_decorator(self):
        max_t = 1e4

        @ReboundParallel
        def setup_sim_decorated(port, sim_id):
            sim = rebound.Simulation()
            sim.add(m=1)
            sim.add(m=1e-3, a=1, e=0.1)
            sim.add(m=1e-3, a=2, e=0.1)
            sim.integrator = "whfast"
            sim.dt = sim.particles[1].P / 20.
            sim.integrate(max_t)
            return sim, sim_id

        jobs = np.arange(0, 10, 1)
        results = setup_sim_decorated.run(jobs, progressbar=False)

        self.assertEqual(len(results), len(jobs))
        self.assertAlmostEqual(results[0][0].t, max_t, 1)
        
        @ReboundParallel
        def setup_sim2_decorated(sim_id):
            sim = rebound.Simulation()
            sim.add(m=1)
            sim.add(m=1e-3, a=1, e=0.1)
            sim.add(m=1e-3, a=2, e=0.1)
            sim.integrator = "whfast"
            sim.dt = sim.particles[1].P / 20.
            sim.integrate(max_t)
            return sim, sim_id

        jobs = np.arange(0, 10, 1)
        results = setup_sim_decorated.run(jobs, progressbar=False)

        self.assertEqual(len(results), len(jobs))
        self.assertAlmostEqual(results[0][0].t, max_t, 1)

    def test_setup(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=5, 
                          port_buffer=15, port0=6000,
                          progressbar=False)

        # test that rebp is the correct type and initialized correctly
        self.assertIsInstance(rebp, ReboundParallel)
        self.assertEqual(rebp.cores, 5)
        self.assertEqual(rebp.port_buffer, 15)
        self.assertEqual(rebp.port0, 6000)

    def test_error(self):
        # test that errors are raised for incorrect types
        
        # test cores arg
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim, cores="Not an int"))
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim, cores=0))
        
        # test progressbar arg
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim, progressbar="No"))
        
        # test port buffer arg
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim, progressbar=False, port_buffer="5"))
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim, progressbar=False, port_buffer=0))

        # test port0 arg
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim,progressbar=False,port_buffer=5,port0="6000"))
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = setup_sim,progressbar=False,port_buffer=5,port0=600_000))

        # test simfunc arg
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = "not a function"))

        # wrong port location
        def simfunc2(sim_id, port):
            pass
        self.assertRaises(TypeError, lambda: ReboundParallel(
            simfunc = simfunc2,progressbar=False,port_buffer=5,port0="6000"))

    def test_verify_before_run(self):
        # test validation of run jobs
        rebp = ReboundParallel(simfunc = setup_sim, cores=5, 
                          port_buffer=15,
                          progressbar=False)
        with self.assertRaises(ValueError):
            rebp.njobs = None
            rebp.verify_before_run()

        with self.assertRaises(ValueError):
            rebp.njobs = 10
            rebp.ports_array = None
            rebp.verify_before_run()

    def test_get_simfunc_type(self):
        rebp = ReboundParallel(simfunc = setup_sim)
        simfunc_port = rebp.simfunc_check()
        self.assertEqual(simfunc_port, True)

        rebp = ReboundParallel(simfunc = setup_sim_noport)
        simfunc_port = rebp.simfunc_check()
        self.assertEqual(simfunc_port, False)

    def test_process_jobs(self):
        jobs = np.arange(0, 10, 1)
        rebp = ReboundParallel(simfunc = setup_sim)
        proc_jobs = rebp.process_jobs(jobs)
        self.assertEqual(len(proc_jobs), len(jobs))

        jobs = [1,2,3]
        proc_jobs = rebp.process_jobs(jobs)
        self.assertEqual(len(proc_jobs), len(jobs))

        jobs = [[1,2],[2,3],[3,4]]
        proc_jobs = rebp.process_jobs(jobs)
        self.assertEqual(len(proc_jobs), len(jobs))

        jobs = np.asarray([[1,2],[2,3],[3,4]])
        proc_jobs = rebp.process_jobs(jobs)
        self.assertEqual(len(proc_jobs), len(jobs))

        jobs = 10
        proc_jobs = rebp.process_jobs(jobs)
        self.assertEqual(proc_jobs, jobs)

        with self.assertRaises(TypeError):
            jobs = "Not a list or int"
            proc_jobs = rebp.process_jobs(jobs)

        with self.assertRaises(TypeError):
            jobs = -1
            proc_jobs = rebp.process_jobs(jobs)

        with self.assertRaises(ValueError):
            jobs = np.zeros((10, 10, 10))
            proc_jobs = rebp.process_jobs(jobs)
        
        with self.assertRaises(ValueError):
            jobs = [[[1,2]],[[2,3]],[[3,4]]]
            proc_jobs = rebp.process_jobs(jobs)


    def test_reset(self):
        rebp = ReboundParallel(simfunc = setup_sim, cores=5, 
                          port_buffer=15,
                          progressbar=False)
        rebp.njobs = 10
        rebp.ports_array = 1234 + np.arange(0, 10, 1)
        rebp.results = [1,2,3]
        rebp.reset_run()

        # test that reset sets njobs, ports_array, and results to None
        self.assertIsNone(rebp.njobs)
        self.assertIsNone(rebp.ports_array)
        self.assertIsNone(rebp.results)

    def test_run(self):
        jobs = np.arange(0, 10, 1)
        rebp = ReboundParallel(simfunc = setup_sim, cores=10)
        results = rebp.run(jobs=jobs)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), len(jobs))
        
    def test_run_noport(self):
        jobs = np.arange(0, 10, 1)

        rebp = ReboundParallel(simfunc = setup_sim_noport, cores=10)
        results = rebp.run(jobs=jobs)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), len(jobs))
    
    def test_run_int(self):
        rebp = ReboundParallel(simfunc = setup_sim_int, cores=10)
        results = rebp.run(jobs=10)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), 10)
    
    def test_run_serial(self):
        jobs = np.arange(0, 3, 1)
        rebp = ReboundParallel(simfunc = setup_sim_noport, cores=1)
        results = rebp.run(jobs=jobs)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), len(jobs))
        
        # check that progressbar and cores arguments are happy
        jobs = np.arange(0, 3, 1)
        rebp = ReboundParallel(simfunc=setup_sim_noport, cores=1, 
                               progressbar=True)
        results = rebp.run(jobs=jobs)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), len(jobs))
        
        # test with jobs as int
        jobs = 3
        rebp = ReboundParallel(simfunc=setup_sim_int, cores=1,
                               progressbar=False)
        results = rebp.run(jobs=jobs)
        results = results

        # test that results are returned for every job
        self.assertEqual(len(results), jobs)

    def test_return(self):
        jobs = np.arange(0, 5, 1)
        rebp = ReboundParallel(simfunc=setup_sim, cores=5, progressbar=True)
        results = rebp.run(jobs=jobs)
        results = results

        # test that each result is a tuple of (sim, sim_id, t_arr, jupiter_xyz)
        self.assertEqual(len(results[0]), 4)

        # test that each jupiter_xyz is of length 100
        self.assertEqual(len(results[0][-1]), 100)

        # test that returned sim is a rebound.Simulation object
        self.assertIsInstance(results[0][0], rebound.Simulation)

        # test that returned sim_id matches jobs id
        sim_id = [result[1] for result in results]
        self.assertEqual(sim_id, jobs.tolist())

        # test that simulations stopped at correct time
        self.assertAlmostEqual(results[0][0].t, results[0][2][-1], 1)

        # test simulation output matches array (Jupiter xyz)
        self.assertTrue(np.allclose(results[0][0].particles[5].xyz, 
                                    results[0][-1][-1]))

if __name__ == "__main__":
    unittest.main()