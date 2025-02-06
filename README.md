##  REBOUNDp(arallel)

#### A package to parallelize and manage parallelized Python [REBOUND](https://github.com/hannorein/rebound) instances

![badge](https://gist.githubusercontent.com/dangcpham/6807845416d284aea12220200073b4ed/raw/483b964bf3526932d5e24f94f58da623c8c1f0b2/test.svg)
---
**Version 0.2**
 - [x] Initiate parallel `REBOUND` instances
 - [x] Progressbar
 - [x] Access `REBOUND` ports
 - [x] Pause, unpause, and stop parallel instances
 - [x] Fetch simulations from ports
 - [x] Separate webserver to manage separate parallel instances
 - [x] Dashboard visualizing running simulations
---
**Dependencies**: 
 - [rebound](https://github.com/hannorein/rebound), [joblib](https://github.com/joblib/joblib)
 - If you want the dashboard (e.g. can only run part two and three below): `REBOUND` version 4+, [flask](https://flask.palletsprojects.com/en/stable/) and [urllib3](https://pypi.org/project/urllib3/)

**Installation**: 
 - clone this repository with `git clone`
 - then `pip install -e .` from within the cloned repo.
 -`pip` coming soon...

**Crash course**: run a simulation in parallel over different eccentricities with a dashboard. In this dashboard, you can view simulations live, start, end, pause, and download REBOUND simulations.
```
import rebound
import numpy as np
from reboundp import ReboundParallel

@ReboundParallel
def rebound_sim(port, ecc):
   sim = rebound.Simulation()
   sim.add(m=1)
   sim.add(m=1e-3, a=1, e=ecc)
   sim.move_to_com()
   
   # IMPORTANT: need this line
   sim.start_server(port=port)
   
   t_arr = np.linspace(0,  1e4,  100)
   planet_xyz = []

   for t in t_arr:
      sim.integrate(t, exact_finish_time=0)
      planet_xyz.append(sim.particles[1].xyz)

      # IMPORTANT: need this line
      if sim.t < t: break

   # IMPORTANT: need this line
   sim.stop_server()
   return sim, planet_xyz

# run setup_sim over 50 different eccentricities
ecc = np.geomspace(0.9, 1-1e-3, 50)

# run using 10 cores
rebound_sim.init_run(jobs=ecc, cores=10, 
                     start_webserver=True, auto_open=True,
                     progressbar=False)
rebound_sim.run()

# after the run
results = rebound_sim.results
# ...whatever else to do with results...
```
---
**Part two**: you hate overhead and just want to run the simulations in parallel quickly.
```
from reboundp import ReboundParallel
import rebound
import numpy as np

@ReboundParallel
def setup_sim(ecc):
   sim = rebound.Simulation()
   sim.add(m=1)
   sim.add(m=1e-3,  a=1,  e=ecc)
   sim.move_to_com()
   sim.integrate(1e5)
   return sim

ecc_arr = np.linspace(0, 0.999, 100)
# run in parallel using all cores
setup_sim.init_run(jobs=ecc_arr, progressbar=True)
setup_sim.run()
results = setup_sim.results
```
This comes with a nice progressbar :):
```
> Progress: [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 100.0% [100/100 Tasks] [02m20s]
```
---
**Part three**: the simplest case, run the same simulation job many times (no parameter).
```
@ReboundParallel
def setup_sim():
   sim = rebound.Simulation()
   sim.add(m=1)
   sim.add(m=1e-3,  a=1,  e=np.random.uniform(0, 1))
   sim.move_to_com()
   sim.integrate(1e5)
   return sim

# run setup_sim 10 times in parallel using 10 cores
# no progressbar, no webserver
setup_sim.init_run(jobs=10, cores=10)
results = setup_sim.run()
```
---
