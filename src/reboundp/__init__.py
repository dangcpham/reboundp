__version__ = 'v0.0.4'
from .parallel import (ReboundParallel)

import os
pymodulepath = os.path.dirname(os.path.abspath(__file__))
pymodulepath = os.path.abspath(os.path.join(pymodulepath, os.pardir))