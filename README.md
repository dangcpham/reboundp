##  REBOUNDp(arallel)

#### A package to parallelize and manage parallelized Python [REBOUND](https://github.com/hannorein/rebound) instances

![badge](https://gist.githubusercontent.com/dangcpham/6807845416d284aea12220200073b4ed/raw/483b964bf3526932d5e24f94f58da623c8c1f0b2/test.svg)
---
**Version 0.0.3**
 - [x] Initiate parallel `REBOUND` instances
 - [x] Progressbar
 - [x] Access `REBOUND` ports
 - [x] Pause, unpause, and stop parallel instances
 - [x] Fetch simulations from ports
 - [ ] Separate webserver to manage separate parallel instances
 - [ ] Dashboard showing CPU usage
 - [ ] Dashboard visualizing running simulations
---
**Dependencies**: [joblib](https://github.com/joblib/joblib)

**Installation**: clone this repository, then `pip install -e .` from within the cloned repo. `pip` soon...

**Quick start**: run a simulation in parallel over different parameters (eccentricity in this case).
```
from reboundp import ReboundParallel

@ReboundParallel
def setup_sim(ecc):
   sim = rebound.Simulation()
   sim.add(m=1)
   sim.add(m=1e-3,  a=1,  e=ecc)
   sim.integrate(1e5)
   return sim

ecc_arr = numpy.linspace(0, 0.999, 300)
# run in parallel using all cores
results = setup_sim.run(ecc_arr, progressbar=True)
```
This comes with a nice progressbar:
```
> Progress: [==================================================] 100.0% [300/300 Tasks] [13.5s]
```
---
**Another usage**: run the same simulation job many times (no parameter).
```
@ReboundParallel
def setup_sim():
   sim = rebound.Simulation()
   sim.add(m=1)
   sim.add(m=1e-3,  a=1,  e=0.1)
   sim.integrate(1e5)
   return sim

# run setup_sim 10 times in parallel using 10 cores
results = setup_sim.run(jobs=10, cores=10)
```
---
***Advanded usage***: run a simulation in parallel, but now we can start/stop/retrieve simulation. This will be much easier in future versions with a separate webserver.
```
def setup_sim(port, _):
   sim = rebound.Simulation()
   sim.add("Solar System")
   
   # IMPORTANT: must enable server to start/stop retrieve simulations
   sim.start_server(port=port)
   
   t_arr = np.linspace(0,  1e4,  100)
   jupiter_xyz = []

   for t in t_arr:
      sim.integrate(t,  exact_finish_time=0)
      if sim.t < t: break # exit early if ended early
      jupiter_xyz.append(sim.particles[5].xyz)

   return sim, sim_id, jupiter_xyz

import threading

# run setup_sim 50 times
jobs = numpy.arange(0, 50, 1)

# run using 10 cores
parallel = ReboundParallel(simfunc = setup_sim, cores=10)

# delayed execution: pause all sims after 0.5 seconds of running
threading.Timer(0.5, parallel.pause_all).start()

# delayed execution: stop all sims after 5 seconds
threading.Timer(5., parallel.end_all).start()

# run now: parallel run
results = parallel.run(jobs=jobs)
```
