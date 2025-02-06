import rebound
from reboundp import ReboundParallel
import numpy as np

# set up sims to run in parallel
@ReboundParallel
def setup_sim(ecc):
    sim = rebound.Simulation()
    sim.add(m=1)
    sim.add(m=1e-3, a=1, e=ecc)
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.
    sim.integrate(1e5)
    xyz = sim.particles[1].xyz 
    return sim, ecc, xyz

# parameter space
ecc_arr = np.linspace(0, 0.999, 200)

# run, use all available cores
setup_sim.init_run(jobs=ecc_arr, progressbar=True)
results = setup_sim.run()

# run, use 1 core
setup_sim.init_run(jobs=ecc_arr, cores=1, progressbar=True)
results = setup_sim.run()

# parsing through results
for result in results:
    sim, ecc, xyz = result
    # print(sim.t, ecc, xyz)