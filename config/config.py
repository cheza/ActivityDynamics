from __future__ import division

import os
from collections import defaultdict
import datetime

from numpy.random.mtrand import poisson
from graph_tool.all import *
from numpy.linalg import eig
import numpy as np
from multiprocessing import Pool

# Change if necessary
r_binary_path = '/usr/bin/RScript'

# Default folder paths. Don't change unless you know what you are doing! Paths are set to create plots within results folder

base_dir = "results/"
graph_binary_dir = base_dir + "graph_binaries/"
graph_source_dir = base_dir + "graph_sources/"
plot_dir = base_dir + "plots/"
graph_dir = base_dir + "graphs/"
r_dir = "R Scripts/"
