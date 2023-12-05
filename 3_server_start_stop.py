import rebound
from reboundp import ReboundParallel
import numpy as np
import threading

def setup_sim(port, sim_id):
    sim = rebound.Simulation()
    sim.add("Solar System")
    sim.integrator = "whfast"
    sim.dt = sim.particles[1].P / 20.
    
    # enable server, need this for reboundp to access sims
    sim.start_server(port=port)

    t_arr = np.linspace(0, 1e4, 100)
    jupiter_xyz = []

    for t in t_arr:
        sim.integrate(t, exact_finish_time=0)
        if sim.t < t: break # need this for reboundp to intervene and end early
        jupiter_xyz.append(sim.particles[5].xyz)

    return sim, sim_id, jupiter_xyz

# set up sims to be run in parallel
jobs = np.arange(0, 50, 1)
rebp = ReboundParallel(simfunc = setup_sim, cores=5, 
                        port_buffer=15,
                        progressbar=False)

# Delayed execution: pause all sims after 0.5 seconds of running
threading.Timer(0.5, rebp.pause_all).start()

# restart all sims after 2 seconds
# threading.Timer(3., court.start_all).start()

# Delayed execution: stop all sims after 5 seconds
threading.Timer(5., rebp.end_all).start()

# run sims immediately
results = rebp.run(jobs=jobs)


for result in results:
    sim, sim_id, jupiter_xyz = result
    print(sim.t)