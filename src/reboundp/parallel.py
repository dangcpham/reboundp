# author: Dang Pham
# last modified: December 2023

# Python standard library
import time, os, warnings, math, inspect, datetime, logging, tempfile, webbrowser, threading, multiprocessing
from typing import List

# Third-party libraries
from joblib import Parallel, delayed
import joblib.parallel

# Check which extra features are available
global FEATURES
FEATURES = []


import rebound

try:
    # only rebound >= 4.0.0 has the webserver feature
    if int(rebound.__version__.split(".")[0]) < 4: raise ImportError
    import urllib3
    FEATURES.append("port")
except ImportError:
    pass

try:
    import flask
    temp_dir = tempfile.TemporaryDirectory()
    FEATURES.append("dashboard")
except ImportError:
    pass

# Local imports
from . import port_utils
from . import utils

REB_STATUS = {-3: "paused", -2: "laststep", -1: "running", 0: "finished",
              1: "generic_error", 2: "no_particles", 3: "encounter",
              4: "escape", 5: "user", 6: "sigint", 7: "collision",}

def print_progress(n_completed_tasks:int, joblib_n_jobs:int, joblib_t0:float):
    progress = (n_completed_tasks+1) / joblib_n_jobs
    time_elapsed = utils.time_format(time.time() - joblib_t0)
    output = f"\rProgress: [{'■'*int(progress * 50):<50}] {(progress*100):.1f}% [{n_completed_tasks+1}/{joblib_n_jobs} Tasks] [{time_elapsed}]"
    print(output, end="", flush=True)

    if n_completed_tasks+1 >= joblib_n_jobs:
        time_started = datetime.datetime.fromtimestamp(joblib_t0).strftime("on %Y-%m-%d at %H:%M:%S")
        print(f"\nFinished running {joblib_n_jobs} tasks. Started {time_started}. Walltime: {utils.time_format(time.time() - joblib_t0)}. \n")


class TimedBatchCompletionCallBack(joblib.parallel.BatchCompletionCallBack):
    """ Custom callback for `joblib.parallel.Parallel` that prints progress to `stdout`."""
     
    def __call__(self, *args, **kwargs):
        if self.parallel.webserver:
            
            urllib3.request("POST", f"{self.parallel.server_path}:{self.parallel.web_port}/update_status/{self.parallel.n_completed_tasks+1}")

        if self.parallel.progressbar:
            print_progress(self.parallel.n_completed_tasks,
                           self.parallel.joblib_n_jobs, 
                           self.parallel.joblib_t0)

        return super().__call__(*args, **kwargs)

class ReboundParallel():
    """ Class structure for running `REBOUND` simulations in parallel.
        Can be used as decorator or as class to construct objects.
        Uses `joblib.Parallel` in the backend to run simulations in parallel.
    """
    def __init__(self, simfunc:callable, 
                 cores:int=None, progressbar:bool=False):
        """ Initialize `REBOUNDParallel` object.

            Parameters
            ----------
            simfunc : callable
                Function to run in parallel.\n

                -------
                Acceptable signatures for `simfunc`:

                1. `simfunc()`                       --- function takes no argument, **cannot** access sims while running
                2. `simfunc(arg1, arg2, ...)`        --- function takes argument(s), **cannot** access sims while running
                3. `simfunc(port)`                   --- function takes no argument, can access sims while running
                4. `simfunc(port, arg1, arg2, ...)`  --- function takes argument(s), can access sims while running
                -------

            cores : int, optional
                Number of cores to use. Must be a positive, non-zero integer. 
                Default is `None`, which will use all but one core.
            progressbar : bool, optional
                Whether to print a progress bar to stdout. Default is `False`.
        """
        self.features = FEATURES
        self.cpu_count = os.cpu_count()
        self.simfunc = simfunc
        self.parallel = None

        # get properties of simfunc
        self.simfunc_port = self.simfunc_check()

        # if cores is not set, use all but one core (last one to run this)
        if cores is None:
            self.cores = self.cpu_count - 1
        else:
            self.cores = cores

        # port things
        self.server_path = "http://localhost"
        self.open_ports = []
        self.progressbar = progressbar

        self.results = None
        self.n_completed_tasks = 0
        
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

        if (simfunc_port == True and 
            list(inspect.signature(self.simfunc).parameters).index("port") != 0):
            raise TypeError(f"port must be the first argument in {self.simfunc.__name__}")

        return simfunc_port

    def validate_init(self):
        """ Validate ReboundParallel object after initialization.
            Raises TypeError if any of the parameters are invalid.
        """
        if type(self.cores) != int or self.cores < 1:
            raise TypeError("cores must be a non-zero positive integer")

        if type(self.progressbar) != bool:
            raise TypeError("progressbar must be a boolean")

    def verify_before_run(self):
        """ Validate ReboundParallel object before parallel running.
            Raises ValueError if any of the parameters are not set.
        """
        if self.njobs is None:
            raise ValueError("njobs must be set before running")

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
        """ Reset ReboundParallel object's parameters: njobs, results."""
        if self.results is not None:
            warnings.warn("Results reset; be careful when using <reboundp.results>", ResourceWarning)

        self.njobs = None
        self.results = None

    def check_port_feature(self):
        """ Check if port feature is available.
            Raises ImportError if port feature is not available.
        """
        if "port" not in self.features:
            raise ImportError("Please install reboundp with pip install reboundp[port] to use this function.")
        return True

    def check_web_feature(self):
        """ Check if dashboard webserver feature is available.
            Raises ImportError if web feature is not available.
        """
        if "dashboard" not in self.features:
            raise ImportError("Please install reboundp with pip install reboundp[dashboard] to use this function.")
        return True

    def webserver_start(self):
        
        # open browser
        server = f"{self.server_path}:{self.web_port}"
        print(f"Starting webserver at {server}")
        if self.web_autoopen:
            proc = threading.Timer(1, webbrowser.open, args=[server])
            proc.start()
            print(f"Opening web browser at {server}")

        # TEMPLATE DIRECTORY
        tmp = os.path.dirname(os.path.abspath(__file__))
        srcdir = os.path.abspath(os.path.join(tmp, os.pardir))
        self.webapp = flask.Flask(__name__, 
                                  static_url_path='', 
                                  static_folder=f"{srcdir}/web_files/static",
                                  template_folder=f"{srcdir}/web_files")

        # disable logging
        log = logging.getLogger('werkzeug')
        log.disabled = True

        # ROUTING
        # main dashboard
        self.webapp.route("/", 
                          methods=['get'])(self.hello_world)
        # status of all sims
        self.webapp.route("/status",
                          methods=['get'])(self.web_sim_status)
        self.webapp.route("/update_status/<int:completed>",
                            methods=['post'])(self.web_update_completed)
        self.webapp.route("/port_open/<int:port>",
                            methods=['post'])(self.web_update_port_open)
        self.webapp.route("/port_close/<int:port>",
                            methods=['post'])(self.web_update_port_close)
        # fetch sim to download
        self.webapp.route("/fetch_sim/<int:port>",
                          methods=['get'])(self.web_fetch_sim)

        # pause
        self.webapp.route("/pause_all",
                          methods=['post'])(self.web_pause_all)
        self.webapp.route("/pause_sim/<int:port>",
                          methods=['get'])(self.web_pause_sim)

        # end
        self.webapp.route("/end_sim/<int:port>", 
                          methods=['get'])(self.web_end_sim) 
        self.webapp.route("/end_all_current", 
                          methods=['post'])(self.web_end_all_current_sims)
        self.webapp.route("/end_all", 
                          methods=['post'])(self.web_end_all)

        #start
        self.webapp.route("/start_sim/<int:port>",
                          methods=['get'])(self.web_start_sim)
        self.webapp.route("/start_all",
                            methods=['post'])(self.web_start_all)

        # START SERVER
        self.webapp.run(host='0.0.0.0', port=self.web_port)
    
    def hello_world(self):
        return flask.render_template(f'index.html')

    def web_sim_status(self):
        sim_list = {}
        n_running = 0
        for port in self.open_ports:
            try:
                _sim = self.fetch_sim(port)
                _sim_status = REB_STATUS[_sim._status]
                sim_list[str(port)] = {"simtime": _sim.t, 
                                       "walltime": utils.time_format(_sim.walltime), 
                                       "status": _sim_status}
                if _sim_status == "running":
                    n_running += 1
            except urllib3.exceptions.MaxRetryError:
                pass

        sim_status = {}
        sim_status = {"total": self.njobs,
                      "cores": self.cores}

        sim_status["completed"] = self.n_completed_tasks
        sim_status["running"] = n_running

        all_sims_status = {}
        all_sims_status["summary"] = sim_status
        all_sims_status["sims"] = sim_list

        return flask.jsonify(all_sims_status)

    def web_fetch_sim(self, port:int):
        try:
            sim = self.fetch_sim(port)
            tmpfilepath = os.path.join(temp_dir.name, f"{port}.bin")
            sim.save_to_file(tmpfilepath)
            return flask.send_file(tmpfilepath, 
                                   mimetype="application/octet-stream")
        except urllib3.exceptions.MaxRetryError:
            return '', 400

    def web_update_port_open(self, port:int):
        self.open_ports.append(port)
        return '', 204

    def web_update_port_close(self, port:int):
        self.open_ports.remove(port)
        return '', 204

    def web_update_completed(self, completed:int):
        self.n_completed_tasks = completed
        return '', 204

    def web_start_sim(self, port:int):
        self.start_sim(port)
        return '', 204

    def web_start_all(self):
        if self.open_ports == []:
            self.run()
        else:
            self.start_all()
        return '', 204

    def web_pause_sim(self, port:int):
        self.pause_sim(port)
        return '', 204

    def web_pause_all(self):
        self.pause_all()
        return '', 204

    def web_end_sim(self, port:int):
        self.end_sim(port)
        return '', 204

    def web_end_all_current_sims(self):
        self.end_all_current_sims()
        return '', 204

    def web_end_all(self):
        self.end_all()
        return '', 204

    def send_space(self, port:int):
        """ Send spacebar command to `REBOUND` server at port to pause simulation.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to send spacebar command to
        """
        self.check_port_feature()
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
        self.check_port_feature()
        urllib3.request(method = "GET",
                        url = f"{self.server_path}:{port}/keyboard/81",
                        retries = 1)

    def fetch_sim(self, port:int):
        """ Fetch simulation object from `REBOUND` server at port.\n
            Under the hood, this function uses `urllib3` to send a GET request to the server.
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
        self.check_port_feature()
        reb_request = urllib3.request("GET", 
                                    f"{self.server_path}:{port}/simulation")
        sim = rebound.Simulation(reb_request.data)

        return sim

    def pause_sim(self, port:int):
        """ Pause simulation at port.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to pause simulation
        """
        try:
            if REB_STATUS[self.fetch_sim(port)._status] == "running":
                self.send_space(port)
        except urllib3.exceptions.MaxRetryError:
            pass

    def pause_all(self):
        """ Pause all simulations available on ports."""
        for port in self.open_ports:
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
        for port in self.open_ports:
            self.start_sim(port)

    def end_sim(self, port:int):
        """ End simulation at port.

            Parameters
            ----------
            port : int
                Port of `REBOUND` server to end simulation
        """
        self.check_port_feature()
        try:
            self.send_q(port)
        except urllib3.exceptions.MaxRetryError:
            pass

    def end_all_current_sims(self):
        """ End all simulations available on REBOUND ports."""
        for port in self.open_ports:
            self.end_sim(port)

    def end_all(self, sleep_timer:float=0.05, batch_buffer:int=10):
        """ End all simulations currently available on ports, repeat until all sims have ended.
            Will wait for `batch_buffer` times the number of batches it took to run the simulations.
            (This is a heuristic to ensure that all sims end.)

            Parameters
            ----------
            sleep_timer : float, optional
                Time to sleep between checking if all sims have ended. Default is 0.01.
            batch_buffer : int, optional
                Batch buffer to ensure that all sims are ended. Default is 10.
        """
        nbatches = int(math.ceil(self.njobs / self.cores)) * batch_buffer
        warnings.warn("Ending all tasks ...", UserWarning)
        for _ in range(nbatches):
            self.end_all_current_sims()
            time.sleep(sleep_timer)

    def init_run(self, jobs, cores:int=None, progressbar:bool=None, 
                 start_webserver:bool=False, auto_open:bool=True):
        """ Initialize jobs to run in parallel.
        
            Parameters
            ----------
            jobs : iterable (int, list or numpy array. If int, must be positive. If iterable, 1 or 2 dimensional.)
                Number of time to run `simfunc`, or list of arguments to distribute to run in parallel.\n
                Will run `simfunc(port, *args)` for each job. 
                Port is automatically assigned by `ReboundParallel`.\n
                `run(jobs)` dispatches jobs as follows:

                1. If `jobs` is an integer, will run `simfunc` for `jobs` number of time.
                2. If `jobs` is a 1D list or numpy array, will run `simfunc(port, *jobs[i])` for each job.
            cores : int, optional
                Number of cores to use. Must be a positive, non-zero integer. 
                Default is None, which will use all but one core.
            progressbar : bool, optional
                Whether to print a progress bar to stdout. 
                If not set, will use value from initialization (default False).
            start_webserver : bool, optional
                Whether to start the dashboard webserver. Default is False.
            auto_open : bool, optional
                Whether to automatically open the dashboard webserver in a web browser. Default is False.

            Returns
            -------
            init_results : bool
                Whether initialization was successful
        """
        
        self.webserver = start_webserver
        self.web_port = port_utils.first_available_port()
        self.web_autoopen = auto_open
        
        # reset before running
        self.reset_run()

        # validate and process jobs argument
        jobs = self.process_jobs(jobs)

        # handle cores and progressbar arguments
        if cores is not None: self.cores = cores
        if progressbar is not None: self.progressbar = progressbar
        if self.progressbar and self.cores == 1: 
            print("Running in serial mode.")
        elif self.progressbar and self.cores > 1:
            print(f"Running in parallel mode with {self.cores} cores.")

        self.jobs = jobs

        # validate
        self.validate_init()

    def __run_parallel(self, parallel)->List:
        """ Run jobs in parallel.

            Parameters
            ----------
            parallel : joblib.Parallel
                Joblib.Parallel object to run jobs in parallel.

            Returns
            -------
            results : List
                List of results from running jobs in parallel        
        """

        if type(self.jobs) == int:
                results = parallel(delayed(self.simfunc)() 
                                    for i in range(self.njobs))
        else:
            if self.simfunc_port:
                func = self.simfunc
                webserver = self.webserver
                server = f"{self.server_path}:{self.web_port}"
                def __wrapper(job):
                    port = port_utils.first_available_port()
                    if webserver: urllib3.request("POST", f"{server}/port_open/{port}")
                    val = func(port, *job)
                    if webserver: urllib3.request("POST", f"{server}/port_close/{port}")
                    return val

                results = parallel(delayed(__wrapper)(self.jobs[i]) 
                    for i in range(self.njobs))
            else:
                results = parallel(delayed(self.simfunc)(*self.jobs[i])
                                for i in range(self.njobs))
        self.results = results

    def __run_serial(self)->List:
        """ Run jobs in serial.

            Returns
            -------
            results : List
                List of results from running jobs in serial
        """
        __serial_n_completed_tasks = 0
        __t0 = time.time()

        # output list
        results = []

        for i in range(self.njobs):
            if type(self.jobs) == int:
                results.append(self.simfunc())
            else:
                if self.simfunc_port:
                    port = port_utils.first_available_port()
                    if self.webserver: urllib3.request("POST", f"{self.server_path}:{self.web_port}/port_open/{port}")

                    results.append(self.simfunc(port, *self.jobs[i]))

                    if self.webserver: urllib3.request("POST", f"{self.server_path}:{self.web_port}/port_close/{port}")
                else:
                    results.append(self.simfunc(*self.jobs[i]))

            if __serial_n_completed_tasks+1 < self.njobs and self.progressbar:
                print_progress(__serial_n_completed_tasks+1, self.njobs, __t0)
            __serial_n_completed_tasks += 1

            if self.webserver: urllib3.request("POST", f"{self.server_path}:{self.web_port}/update_status/{__serial_n_completed_tasks+1}")

            self.n_completed_tasks = __serial_n_completed_tasks
        self.results = results
            
    def run(self,  *joblib_args, **joblib_kwargs)->List:
        """ Run jobs in parallel.

            Parameters
            ----------
            *joblib_args : optional
                Additional arguments to pass to joblib.Parallel
            **joblib_kwargs : optional
                Additional keyword arguments to pass to joblib.Parallel

            Returns
            -------
            results : List
                List of results from running jobs in parallel        
        """
        # start webserver
        if self.webserver and self.check_web_feature():
            webproc = multiprocessing.Process(target=self.webserver_start)
            webproc.start()

        if self.cores == 1:
            # check that server is online, if not wait a little
            if self.webserver:
                try: urllib3.request("GET", f"{self.server_path}:{self.web_port}")
                except urllib3.exceptions.MaxRetryError:
                    time.sleep(1)
            self.__run_serial()
        else:
            # run jobs in parallel
            joblib.parallel.BatchCompletionCallBack = TimedBatchCompletionCallBack
            self.parallel = Parallel(n_jobs=self.cores, 
                                     *joblib_args, **joblib_kwargs)

            # track progress
            self.parallel.joblib_n_jobs = self.njobs
            self.parallel.progressbar = self.progressbar
            self.parallel.joblib_t0 = time.time()
            self.parallel.webserver = self.webserver
            self.parallel.server_path = self.server_path
            self.parallel.web_port = self.web_port
            self.__run_parallel(self.parallel)
        print("Simulations done...")
        if self.webserver:
            time.sleep(1)
            webproc.terminate()
        return self.results
