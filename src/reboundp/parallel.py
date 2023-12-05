"""
    author: Dang Pham
    last modified: December 2023
"""

# Python standard library
import time, os, warnings, math, inspect, datetime
from typing import List

# Third-party libraries
from joblib import Parallel, delayed
import joblib.parallel
import rebound
import urllib3

# Local imports
from . import port_utils
from . import utils

REB_STATUS = {-3: "paused", -2: "laststep", -1: "running", 0: "finished",
              1: "generic_error", 2: "no_particles", 3: "encounter",
              4: "escape", 5: "user", 6: "sigint", 7: "collision",}

class TimedBatchCompletionCallBack(joblib.parallel.BatchCompletionCallBack):
    """ Custom callback for `joblib.parallel.Parallel` that prints progress to `stdout`."""    
    def __call__(self, *args, **kwargs):
        if self.parallel.progressbar:
            progress = (self.parallel.n_completed_tasks+1) / self.parallel.joblib_n_jobs
            time_elapsed = utils.time_format(time.time() - self.parallel.joblib_t0)
            output = f"\rProgress: [{'='*int(progress * 50):<50}] {(progress*100):.1f}% [{self.parallel.n_completed_tasks+1}/{self.parallel.joblib_n_jobs} Tasks] [{time_elapsed}]"
            print(output, end="", flush=True)

            if self.parallel.n_completed_tasks+1 >= self.parallel.joblib_n_jobs:
                time_started = datetime.datetime.fromtimestamp(self.parallel.joblib_t0).strftime("%Y-%m-%d %Hh%Mm%Ss")
                print(f"\nFinished running {self.parallel.joblib_n_jobs} tasks. Started at {time_started}. Walltime: {utils.time_format(time.time() - self.parallel.joblib_t0)}. \n")

        return super().__call__(*args, **kwargs)

class ReboundParallel():
    """ Class structure for running `REBOUND` simulations in parallel.
        Can be used as decorator or as class to construct objects.
        Uses `joblib.Parallel` in the backend to run simulations in parallel.
    """
    def __init__(self, simfunc:callable, 
                 cores:int=None, progressbar:bool=False, 
                 port_buffer:int=5, port0:int=None):
        """ Initialize `REBOUNDParallel` object.

            Parameters
            ----------
            simfunc : callable
                Function to run in parallel.\n

                -------
                Acceptable signatures for `simfunc`:

                1. `simfunc()`                   --- function takes no argument, **cannot** access sims while running
                2. `simfunc(arg1, arg2, ...)`        --- function takes argument(s), **cannot** access sims while running
                3. `simfunc(port)`               --- function takes no argument, can access sims while running
                4. `simfunc(port, arg1, arg2, ...)`  --- function takes argument(s), can access sims while running
                -------

            cores : int, optional
                Number of cores to use. Must be a positive, non-zero integer. 
                Default is `None`, which will use all but one core.
            progressbar : bool, optional
                Whether to print a progress bar to stdout. Default is `False`.
            port_buffer : int, optional
                A buffer (we reserve more ports than we need) to avoid overusing ports.
                Default is `5`.
            port0 : int, optional
                First port to use. Must be a positive, non-zero integer, between `1024` and `65535`.
                Default is `None`, which will automatically determine and use first available port..
        """
        self.cpu_count = os.cpu_count()
        self.simfunc = simfunc

        # get properties of simfunc
        self.simfunc_port = self.simfunc_check()

        # if cores is not set, use all but one core (last one to run this)
        if cores is None:
            self.cores = self.cpu_count - 1
        else:
            self.cores = cores

        # port things
        self.port_buffer = port_buffer
        self.server_path = "http://localhost"
        self.progressbar = progressbar

        # if port0 is not set, use first available port
        if port0 is None: 
            self.port0 = port_utils.first_available_port()
        else:
            self.port0 = port0

        self.results = None
        self.validate_init()

    def simfunc_check(self)->bool:
        """ Get properties of `simfunc` and check if simfunc is in valid form.
            Returns whether port is an argument.

            Returns:
            --------
            simfunc_port : bool
                Whether port is an argument in `simfunc`
        """
        if callable(self.simfunc) == False:
            raise TypeError(f"simfunc must be a function. {type(self.simfunc)} was passed.")

        if inspect.signature(self.simfunc).parameters.get("port") is None:
            simfunc_port = False
        else:
            simfunc_port = True

        if simfunc_port == True and list(inspect.signature(self.simfunc).parameters).index("port") != 0:
            raise TypeError(f"port must be the first argument in {self.simfunc.__name__}")

        return simfunc_port

    def validate_init(self):
        """ Validate ReboundParallel object after initialization.
            Raises TypeError if any of the parameters are invalid.
        """
        if self.port0 > 65535 or self.port0 < 1024:
            raise TypeError("port0 must be a positive integer between 1024 and 65535")

        if type(self.cores) != int or self.cores < 1:
            raise TypeError("cores must be a non-zero positive integer")

        if type(self.port_buffer) != int or self.port_buffer < 1:
            raise TypeError("port_buffer must be a non-zero positive integer")

        if type(self.progressbar) != bool:
            raise TypeError("progressbar must be a boolean")

    def verify_before_run(self):
        """ Validate ReboundParallel object before parallel running.
            Raises ValueError if any of the parameters are not set.
        """
        if self.njobs is None:
            raise ValueError("njobs must be set before running")
        if self.ports_array is None:
            raise ValueError("ports_array must be set before running")

    def process_jobs(self, jobs):
        """ Process jobs argument. Check if jobs is an integer or an iterable.
            If integer, return a list of length `njobs`.
            If iterable and 1D, return a (0,1) array (2D).

            Parameters
            ----------
            jobs: int, list, numpy array
                Number of jobs to run, or list of arguments to run in parallel.

            Returns
            -------
            __jobs : int, list or numpy array
                Number of jobs to run, or list of arguments to run in parallel (processed).

        """
        # validate jobs type
        if type(jobs) == int and jobs > 0:
            self.njobs = jobs
        elif utils.is_list(jobs):
            self.njobs = len(jobs)
        else:
            raise TypeError("jobs must be a positive integer, list, or numpy array")

        # if jobs is an integer, create a list of length njobs
        if type(jobs) == int:
            __jobs = jobs

        # if jobs is a list
        elif type(jobs) == list:
            # if jobs is a 1D list create a (0,1) list (2 dimensional)
            if len(utils.dim(jobs)) == 1:
                __jobs = [[jobs[i]] for i in range(self.njobs)]
            # if jobs is a 2D list or numpy array, return as is
            elif len(utils.dim(jobs)) == 2:
                __jobs = jobs
            else:
                raise ValueError(f"jobs must be a 1 or 2 dimensional array")

        # if jobs is a numpy array (or something else similar)
        else:
            # if jobs is a 1D list create a (0,1) list (2 dimensional)
            if jobs.ndim == 1:
                __jobs = [[jobs[i]] for i in range(self.njobs)]
            # if jobs is a 2D list or numpy array, return as is
            elif jobs.ndim == 2:
                __jobs = jobs
            else:
                raise ValueError(f"jobs must be a 1 or 2 dimensional array,")
    
        return __jobs

    def reset_run(self):
        """ Reset ReboundParallel object's parameters: njobs, ports_array, results."""
        if self.results is not None:
            warnings.warn("Results reset; be careful when using <reboundp.results>", ResourceWarning)

        self.njobs = None
        self.ports_array = None
        self.results = None

    def current_open_ports(self)->List[int]:
        """ Get list of ports currently in use by `REBOUND` servers.

            Parameters
            ----------
            None

            Returns
            -------
            open_ports : list
                List of ports currently in use by `REBOUND` servers
        """
        open_ports = port_utils.get_rebound_ports(min(self.ports_array), 
                                       max(self.ports_array) + 2,
                                       server_path=self.server_path)
        return open_ports

    def send_space(self, port:int):
        """ Send spacebar command to `REBOUND` server at port to pause simulation.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to send spacebar command to
        """
        urllib3.request(method = "GET",
                        url = f"{self.server_path}:{port}/keyboard/32",
                        retries = False)

    def send_q(self, port:int):
        """ Send q command to `REBOUND` server at port to end simulation.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to send q command to
        """
        urllib3.request(method = "GET",
                        url = f"{self.server_path}:{port}/keyboard/81",
                        retries = 1)

    def fetch_sim(self, port:int)->rebound.Simulation:
        """ Fetch simulation object from `REBOUND` server at port.\n
            Under the hood, this function uses `urllib` to send a GET request to the server.
            Then, it loads the retrieved bytes data into a `rebound.Simulation` object.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to fetch simulation from

            Returns
            -------
            sim : rebound.Simulation
                Simulation object from `REBOUND` server at port
        """
        reb_request = urllib3.request("GET", f"{self.server_path}:{port}/simulation")
        sim = rebound.Simulation(reb_request.data)

        return sim

    def pause_sim(self, port:int):
        """ Pause simulation at port.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to pause simulation
        """
        if REB_STATUS[self.fetch_sim(port)._status] == "running":
            self.send_space(port)

    def pause_all(self):
        """ Pause all simulations available on ports."""
        for port in self.current_open_ports():
            self.pause_sim(port)

    def start_sim(self, port:int):
        """ Unpause simulation at port.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to unpause simulation
        """
        if REB_STATUS[self.fetch_sim(port)._status] == "paused":
            self.send_space(port)

    def start_all(self):
        """ Unpause all simulations available on ports."""
        for port in self.current_open_ports():
            self.start_sim(port)

    def end_sim(self, port:int):
        """ End simulation at port.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to end simulation
        """
        try:
            self.send_q(port)
        except urllib3.exceptions.MaxRetryError:
            pass

    def end_all_current_sims(self):
        """ End all simulations available on REBOUND ports."""
        for port in self.current_open_ports():
            self.end_sim(port)

    def end_all(self, sleep_timer:float=0.05, batch_buffer:int=5):
        """ End all simulations currently available on ports, repeat until all sims have ended.
            Will wait for 5 times the number of batches it took to run the simulations.
            (This is a heuristic to ensure that all sims end.)

            Parameters
            ----------
            sleep_timer : float, optional
                Time to sleep between checking if all sims have ended. Default is 0.01.
            batch_buffer : int, optional
                Batch buffer to ensure that all sims are ended. Default is 5.
        """
        nbatches = int(math.ceil(self.njobs / self.cores)) * batch_buffer
        warnings.warn("Ending all tasks ...", UserWarning)
        for _ in range(nbatches):
            self.end_all_current_sims()
            time.sleep(sleep_timer)

    def run(self, jobs, cores:int=None, progressbar:bool=None, *joblib_args, **joblib_kwargs)->List:
        """ Run jobs in parallel.

            Parameters
            ----------
            jobs : iterable (int, list or numpy array. If int, must be positive. If iterable, 1 or 2 dimensional.)
                Number of time to run `simfunc`, or list of arguments to distribute to run in parallel.\n
                Will run `simfunc(port, *args)` for each job. 
                Port is automatically assigned by `ReboundParallel`.\n
                `run(jobs)` dispatches jobs as follows:

                1. If `jobs` is an integer, will run `simfunc` for `jobs` number of time.
                1. If `jobs` is a 1D list or numpy array, will run `simfunc(port, *jobs[i])` for each job.
            cores : int, optional
                Number of cores to use. Must be a positive, non-zero integer. 
                Default is None, which will use all but one core.
            progressbar : bool, optional
                Whether to print a progress bar to stdout. 
                If not set, will use value from initialization (default False).
            *joblib_args : optional
                Additional arguments to pass to joblib.Parallel
            **joblib_kwargs : optional
                Additional keyword arguments to pass to joblib.Parallel

            Returns
            -------
            results : List
                List of results from running jobs in parallel        
        """
        # reset before running
        self.reset_run()

        # validate and process jobs argument
        jobs = self.process_jobs(jobs)

        # handle cores and progressbar arguments
        if cores is not None: self.cores = cores
        if progressbar is not None: self.progressbar = progressbar

        # assign ports to jobs
        job_list = list(range(0, self.njobs))
        port1 = self.port0 + 1
        core_buffer = self.cores * self.port_buffer
        self.ports_array = [(port1 + (port % core_buffer)) for port in job_list]

        # validate before running
        self.validate_init()
        self.verify_before_run()

        # run jobs in parallel
        joblib.parallel.BatchCompletionCallBack = TimedBatchCompletionCallBack
        with Parallel(n_jobs=self.cores, *joblib_args, **joblib_kwargs) as parallel:
            parallel.joblib_n_jobs = self.njobs
            parallel.progressbar = self.progressbar
            parallel.joblib_t0 = time.time()

            if type(jobs) == int:
                results = parallel(delayed(self.simfunc)() for i in range(self.njobs))
            else:
                if self.simfunc_port:
                    results = parallel(delayed(self.simfunc)(self.ports_array[i], *jobs[i]) 
                                    for i in range(self.njobs))
                else:
                    results = parallel(delayed(self.simfunc)(*jobs[i])
                                    for i in range(self.njobs))

        self.results = results
        return results
