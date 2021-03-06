import config.config as config

import os as os
import math
import random
from lib.network import *
from collections import defaultdict
import datetime
from scipy.stats import sem
import numpy as np
import scipy as sp
from decimal import *
from textwrap import wrap
import pandas as pd

# set level of debug output
DEBUG_LEVEL = 0


# retrieve parameters stored in binary graph file
def get_network_details(graph_name, run=0, path=config.graph_binary_dir):
    graph = load_graph(path + "GT/" + graph_name + "/" + graph_name + "_run_" + str(run) + ".gt")
    ratios = graph.graph_properties["ratios"]
    deltataus = graph.graph_properties["deltatau"]
    deltapsi = graph.graph_properties["deltapsi"]
    ew = graph.graph_properties["top_eigenvalues"]
    random_inits = graph.graph_properties["runs"]
    store_iterations = graph.graph_properties["store_iterations"]
    try:
        a_cs = graph.graph_properties["a_cs"]
        cas = graph.graph_properties["activity_per_month"]
    except:
        debug_msg(" --> Could not load empirical data!")
        cas = []
        a_cs = []
    return graph, ratios, deltataus, deltapsi, graph_name, store_iterations, cas, ew, random_inits, a_cs


def prepare_folders():
    flist = [config.graph_binary_dir,
             config.graph_binary_dir + "GT/",
             config.graph_binary_dir + "ratios/",
             config.graph_binary_dir + "empirical_data/",
             config.graph_source_dir + "empirical_results/",
             config.graph_source_dir,
             config.graph_source_dir + "weights",
             config.graph_dir,
             config.plot_dir,
             config.plot_dir + "eigenvalues",
             config.plot_dir + "functions",
             config.plot_dir + "weights_over_time",
             config.plot_dir + "average_weights_over_tau",
             config.plot_dir + "empirical_results"]

    for fname in flist:
        create_folder(fname)


def create_folder(folder):
    if not os.path.exists(folder):
        debug_msg("Created folder: {}".format(folder))
        os.makedirs(folder)


# helper functions to get filename
def get_weights_fn(store_iterations, deltatau, run, graph_name, ratio):
    return config.graph_source_dir + "weights/" + graph_name + "/" + graph_name + \
           "_" + str(store_iterations).replace(".", "") + "_" + \
           str(deltatau).replace(".", "") + "_" + str(ratio).replace(".", "") + "_run_" + str(run) + "_weights.txt"


# helper function to get filename for intrinsic activity
def get_intrinsic_weights_fn(store_iterations, deltatau, run, graph_name, ratio):
    return config.graph_source_dir + "weights/" + graph_name + "/" + graph_name + \
           "_" + str(store_iterations).replace(".", "") + "_" + \
           str(deltatau).replace(".", "") + "_" + str(ratio).replace(".", "") + "_run_" + str(run) + "_intrinsic.txt"


# helper function to get filename for extrinsic activity
def get_extrinsic_weights_fn(store_iterations, deltatau, run, graph_name, ratio):
    return config.graph_source_dir + "weights/" + graph_name + "/" + graph_name + \
           "_" + str(store_iterations).replace(".", "") + "_" + \
           str(deltatau).replace(".", "") + "_" + str(ratio).replace(".", "") + "_run_" + str(run) + "_extrinsic.txt"


# plot empirical activity (left y-axis) vs. observed activity (right y-axis) for empirical datasets
def empirical_result_plot(graph_name, run=0):
    import subprocess
    import os
    source_path = os.path.abspath(config.graph_source_dir + "empirical_results/" + graph_name + ".txt")
    out_file = open(source_path, "wb")
    debug_msg("  >>> Creating empirical result plot", level=0)
    graph, ratios, deltatau, deltapsi, graph_name, store_iterations, \
    cas, ew, random_inits, a_cs = get_network_details(graph_name, run)
    pipe_vals = [str(deltatau), "%.4f" % deltapsi, "%.2f" % a_cs[0], "%.2f" % ew[0]]
    debug_msg("   ** Preparing Ratios", level=0)
    x_ratios = [(float(x)+1) for x in range(len(ratios))]
    y_ratios = ratios
    out_file.write(("\t").join(["%.8f" % x for x in x_ratios])+"\n")
    out_file.write(("\t").join(["%.8f" % x for x in y_ratios])+"\n")
    debug_msg("   ** Preparing Average Activities", level=0)
    fpath = get_weights_fn(store_iterations, deltatau, run, graph_name, ratios[0])
    epath = os.path.abspath(get_extrinsic_weights_fn(store_iterations, deltatau, run, graph_name, ratios[0]))
    ipath = os.path.abspath(get_intrinsic_weights_fn(store_iterations, deltatau, run, graph_name, ratios[0]))
    x_activity = []
    y_activity = []
    pf = open(fpath, "rb")
    for lidx, l in enumerate(pf):
        x_activity.append((float(lidx)+1)*deltatau/deltapsi*store_iterations)
        y_activity.append(sum([float(x) for x in l.split("\t")]))
    pf.close()
    out_file.write(("\t").join(["%.8f" % x for x in x_activity])+"\n")
    out_file.write(("\t").join(["%.8f" % x for x in y_activity])+"\n")

    debug_msg("   ** Preparing Real Activities", level=0)
    y_real_act = cas
    x_real_act = range(len(cas))
    out_file.write(("\t").join(["%.8f" % x for x in x_real_act])+"\n")
    out_file.write(("\t").join(["%.8f" % x for x in y_real_act])+"\n")
    out_file.close()
    debug_msg("   ** Calling empirical_plots.R", level=0)
    r_script_path = os.path.abspath(config.r_dir + 'empirical_plots.R')
    wd = r_script_path.replace("R Scripts/empirical_plots.R", "") + config.plot_dir + "empirical_results/"
    subprocess.call([config.r_binary_path, r_script_path, wd, source_path, pipe_vals[0], pipe_vals[1], pipe_vals[2],
                     pipe_vals[3], graph_name, ipath, epath], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
    debug_msg("   ** Done", level=0)


# plot simulated ratios and kappa 1 (for empirical datasets)
def plot_empirical_ratios(graph_name, run=0):
    debug_msg("  >>> Drawing Ratios over Tau", level=0)
    graph, ratios, deltatau, deltapsi, graph_name, store_iterations, cas, ew, random_inits, a_cs = get_network_details(graph_name, run)
    storage_folder = config.plot_dir + "ratios_over_time/" + graph_name + "/"
    debug_msg("    ++ Processing graph = {}, deltatau = {}, deltapsi = {}".format(graph_name, deltatau, deltapsi),
              level=0)
    x_vals = [(float(x)+1) for x in range(len(ratios))]
    y_vals = ratios
    plt.plot(x_vals, y_vals, alpha=0.5)
    max_x = max(x_vals)
    plt.plot([0, max_x], [ew[0], ew[0]], 'k-', lw=1)
    plt.title("Ratio " +
              r"$(\frac{\lambda}{\mu})$" +
              " over " +
              r"$\tau$" +
              "\n" +
              r"$\Delta\tau$"+"={}, ".format(deltatau) +
              r"$\Delta\psi$"+"={}, ".format("%.4f" % deltapsi) +
              r"$a_c$"+"={}".format("%.2f" % a_cs[0]) +
              r", $\kappa_1$={}".format("%.2f" % ew[0])
    )
    plt.xlabel(r"$\tau$ (in Months)")
    plt.ylabel("Ratio "+ r"$(\frac{\lambda}{\mu})$")
    ax = plt.axes()
    ax.grid(color="gray")
    plt.savefig(storage_folder + graph_name + "_{}_{}_empirical_ratios.png".format(store_iterations,
                                                                                   str(deltatau).replace(".", "")))
    plt.close("all")


# plot average activity over tau (for empirical networks)
def avrg_activity_over_tau_empirical(graph_name, run=0):
    debug_msg("  >>> Drawing Average Activity over Tau", level=0)
    graph, ratios, deltatau, deltapsi, graph_name, store_iterations, cas, \
    ew, random_inits, a_cs = get_network_details(graph_name, run)
    storage_folder = config.plot_dir + "average_weights_over_tau/" + graph_name + "/"
    debug_msg("    ++ Processing graph = {}, deltatau = {}, deltapsi = {}".format(graph_name, deltatau, deltapsi),
              level=0)
    fpath = get_weights_fn(store_iterations, deltatau, run, graph_name, ratios[0])
    plt.figure()
    x_vals = []
    y_vals = []
    pf = open(fpath, "rb")
    for lidx, l in enumerate(pf):
        x_vals.append((float(lidx)+1)*deltatau/deltapsi*store_iterations)
        print sum([float(x) for x in l.split("\t")])
        y_vals.append(sum([float(x) for x in l.split("\t")]))
    plt.plot(x_vals, y_vals, alpha=0.5)
    pf.close()
    plt.title("Activity in Network over "+r"$\tau$"+"\n"
              +r"$\Delta\tau$"+"={}, ".format(deltatau)
              +r"$\Delta\psi$"+"={}, ".format("%.4f" % deltapsi)
              +r"$a_c=${}".format("%.2f" % a_cs[0]))
    plt.xlabel(r"$\tau$ (in Months)")
    plt.ylabel("Average Activity per Network")
    ax = plt.axes()
    ax.grid(color="gray")
    plt.savefig(storage_folder + graph_name + "_" + str(store_iterations) +
                "_iterations_over_time_{}_{}_empirical.png".format(store_iterations, str(deltatau).replace(".", "")))
    plt.close("all")


# plot average activity over tau (for synthetical datasets)
def avrg_activity_over_tau(graph_name):
    debug_msg("  >>> Drawing Average Activity over Tau", level=0)
    graph, ratios, deltatau, deltapsi, graph_name, store_iterations, cas, \
    ew, random_inits, a_cs = get_network_details(graph_name)
    storage_folder = config.plot_dir + "average_weights_over_tau/" + graph_name + "/"
    for ratio in ratios:
        x_avrg = []
        y_avrg = []
        for run in xrange(random_inits):
            debug_msg("  ++ Processing ratio = {}, deltatau = {}".format(ratio, deltatau), level=0)
            fpath = get_weights_fn(store_iterations, deltatau, run, graph_name, ratio)
            weights_df = pd.read_csv(fpath, sep="\t", header=None)
            means = weights_df.mean(axis=1)
            if len(y_avrg) == 0:
                y_avrg = means[:]
                for lidx in xrange(len(y_avrg)):
                    x_avrg.append(float(lidx)*(deltatau/deltapsi)*store_iterations)
            else:
                y_avrg += means[:]
        plt.figure()
        pf = open(fpath, "rb")
        plt.plot(x_avrg, y_avrg/random_inits, alpha=0.5)
        pf.close()
        plt.title("Activity in Network over "+r"$\tau$"+"\n"+r"$\frac{\lambda}{\mu}$"+
                  "={},".format(ratio)+r"$\Delta\tau$"+"={}, ".format(deltatau)+
                  r"$\Delta\psi$"+"={}".format(deltapsi))
        plt.xlabel(r"$\tau$")
        plt.ylabel("Average Activity per Network")
        plt.subplots_adjust(bottom=0.15)
        ax = plt.axes()
        ax.grid(color="gray")
        plt.savefig(storage_folder + graph_name + "_" + str(store_iterations) +
                    "_iterations_over_time_{}_{}.png".format(str(ratio).replace(".", ""),
                                                             str(deltatau).replace(".", "")))
        plt.close("all")


# function to call R Script for plotting weights over time
def plot_weights_over_time(graph_name):
    import subprocess
    import os

    debug_msg("  >>> Drawing Weights over Time plot", level=0)
    graph, ratios, deltatau, deltapsi, graph_name, store_iterations, cas, ew, random_inits, a_cs = get_network_details(graph_name)

    for ratio in ratios:
        y_vals = []
        x_vals = [0.0]
        out_path = os.path.abspath(config.plot_dir + "weights_over_time/" + graph_name + "/"+graph_name+"_"+
                                   str(ratio).replace(".", "")+".txt")
        out_file = open(out_path, "wb")
        for run in xrange(random_inits):
            debug_msg("  ++ Processing ratio = {}, deltatau = {}".format(ratio, deltatau), level=0)
            fpath = get_weights_fn(store_iterations, deltatau, run, graph_name, ratio)
            if run == 0:
                y_vals = pd.read_csv(fpath, sep="\t", header=None)
            else:
                y = pd.read_csv(fpath, sep="\t", header=None)
                y_vals = y_vals.add(y).fillna(method="ffill", axis=1)
        for lidx in xrange(len(y_vals)):
            x_vals.append(float(lidx)*(deltatau/deltapsi)*store_iterations)
        y_vals = y_vals.div(random_inits).fillna(method="ffill", axis=1).as_matrix()
        out_file.write(("\t").join(["%.8f" % xn for xn in x_vals])+"\n")
        for seq in y_vals:
            out_file.write(("\t").join([str(x) for x in seq])+"\n")
        out_file.close()
        debug_msg("  ** Calling weights_over_time.R", level=0)
        r_script_path = os.path.abspath(config.r_dir + 'weights_over_time.R')
        wd = r_script_path.replace("R Scripts/weights_over_time.R", "") + \
             "results/plots/weights_over_time/"
        subprocess.call([config.r_binary_path, r_script_path, wd, out_path, str(ratio), str(deltatau), graph_name,
                         "%.2f" % ew[0]], stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'))
        debug_msg("  ** Done", level=0)

# debug output
def debug_msg(msg, level=0):
    if level <= DEBUG_LEVEL:
        print "  \x1b[33m-UTL-\x1b[00m [\x1b[36m{}\x1b[00m] \x1b[35m{}\x1b[00m".format(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"), msg)

