import rebound
from reboundp import ReboundParallel
import numpy as np

@ReboundParallel
def setup_sim():
    sim = rebound.Simulation()
    sim.add(m=1)
    sim.add(m=1e-3, a=1, e=0.999)
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.
    sim.integrate(1e5)
    xyz = sim.particles[1].xyz 
    return sim, xyz

# run a job 10 times, use 10 cores
results = setup_sim.run(jobs=10, cores=10)

for result in results:
    sim, xyz = result
    print(sim.t, xyz)