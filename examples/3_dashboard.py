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
   
   t_arr = np.linspace(0,  1e5,  100)
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
print(len(results))
