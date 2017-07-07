# # !/usr/bin/python
# # -*- coding: utf-8 -*-
# #
# # simu-plot -- Plot a workload schedule
# #
# # Given a system configuration, a workload description, and a schedule as
# # generated by simulation, this program generates a plot displaying the
# # amount of gpus used by each job over time, as well as submission times
# # for each job in the workload.
# #
# # Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>
#

import os
import copy
import json
import math
import random
import argparse
import itertools
import matplotlib
import configparser
import pandas as pd
import seaborn as sns
import scipy.stats as stats
import matplotlib.pyplot as plt
from collections import OrderedDict
from matplotlib.ticker import AutoMinorLocator

import numpy as np
import seaborn as sns

from utils import nv_demon
from utils import nvlink
from utils import square_plot


def workloads_exec_time_add_value(workload_list, name, job, gpus_list, start_time, end_time, submitted_time):
    if name not in workload_list:
        workload_list[name] = dict()
    if job not in workload_list[name]:
        workload_list[name][job] = dict()
        exec_time = end_time - start_time
        exec_time_submitted = end_time - submitted_time

        workload_list[name][job]['gpus'] = gpus_list
        workload_list[name][job]['start_time'] = start_time
        workload_list[name][job]['end_time'] = end_time
        workload_list[name][job]['submitted_time'] = submitted_time
        workload_list[name][job]['exec_time'] = exec_time
        workload_list[name][job]['exec_time_submitted'] = exec_time_submitted
    return workload_list


def get_fig_index():
    return itertools.cycle(['(c)', '(d)', '(b)', '(a)', '(e)', '(f)', '(g)', '(h)'])


def get_colors():
    return itertools.cycle(['k', 'g', 'r', 'b', 'm', 'y', 'c'])


def get_lines_format():
    return itertools.cycle(["--", "-.", ":", "-"])


def get_colors2():
    return itertools.cycle(['#f2b1bc', '#02e0bd', '#7cc8f0', '#9083de', '#07a998', '#5a71ff', '#224fc2', '#19f2fb',
                            '#8e9e1f', '#3266c8', '#2b2c08', '#975ce0', '#e1c295', '#95e4c9', '#5d160e', '#4b5241',
                            '#7a55f8', '#ac3320', '#58aa2d', '#953164'])


def get_pattern():
    return itertools.cycle(['/', 'o', 'x', '-', '+', 'O', '.', '*'])


folders = list()
for root, directories, files in os.walk("../../results/"):
# for root, directories, files in os.walk("../../results-bk/workloads-5/"):
    if not "real" in root and not "600" in root:
        if 'placement_stats.json' in files:
            print "folder: ", root, files
            folders.append(root + "/")

sys_config = configparser.ConfigParser(delimiters=("="))
sys_config.read("../../etc/configs/sys-config.ini")

job_profiles = json.load(
                open("../../data/profiles/" + json.loads(sys_config.get("workload", "profile")) + ".json", "r"))


# logging.basicConfig(format="%(message)s", level=logging.ERROR)
length = sys_config.getfloat("simulator", "length")
period = sys_config.getfloat("simulator", "period")
digits = sys_config.getint("simulator", "digits")
window_min = sys_config.getfloat("plot", "window_min")
window_max = sys_config.getfloat("plot", "window_max")
submissions = sys_config.getboolean("plot", "submissions")
workload_file = json.loads(sys_config.get("workload", "workload_file"))
offset = int(math.floor(window_min / period))

workloads_exec_time = dict()
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--sched_config", dest="c", required=False,
                help="System configuration file", default="../../etc/configs/sched_config-")
ap.add_argument("-w", "--workload", dest="w", required=False,
                help="JSON workload file", default="../../data/")
ap.add_argument("-s", "--schedule", dest="s", required=False,
                help="JSON schedule file", default="sched_stats.json")
ap.add_argument("-p", "--placement", dest="p", required=False,
                help="JSON schedule file", default="placement_stats.json")
ap.add_argument("-t", "--stats", dest="t", required=False,
                help="JSON stats file", default="system_stats.json")
args = ap.parse_args()

with open(args.w + workload_file + ".json") as w:
    workload = json.load(w)

sns.set_context("paper", font_scale=3)

fig_indexs = get_fig_index()
postponded = False
num_gpus = 0

for result_folder in folders:
    # result_folder = folders[0]
    lines_format = get_lines_format()
    colors = get_colors()
    patterns = get_pattern()
    values = result_folder.split("/")
    algo_name = values[5].split("-")

    if not postponded:
        if "bf" in algo_name:
            folders.append(result_folder)
            postponded = True
            # continue
    # print algo_name
    if "utilityaware" not in algo_name:
        algo_name = algo_name[len(algo_name) - 1].upper()
    else:
        postpone = algo_name[len(algo_name) - 1]
        algo_name = algo_name[len(algo_name) - 5].upper()
        if postpone == 'True':
            algo_name += "-P"

    args = ap.parse_args()
    sched_config = configparser.ConfigParser(delimiters=("="))
    # print args.c + algo_name + '.ini'
    sched_config.read(args.c + algo_name + '.ini')

    args = ap.parse_args()

    with open(result_folder+args.s) as s:
        scheduler_stats = json.load(s)

    with open(result_folder+args.p) as p:
        placement_stats = json.load(p)

    with open(result_folder+args.t) as t:
        system_stats = json.load(t)

    scheduler_stats = sorted(scheduler_stats.iteritems(), key=lambda t: t[0], reverse=False)
    x = list()
    y = list()
    for file in scheduler_stats:
        # print file
        # if int(file[1]["num_jobs"]) > 0:
        x.append(file[0])
        y.append(float(file[1]["sched_time"]))

    print algo_name
    # from pprint import pprint
    # pprint(y)
    arr = np.array(y)
    print arr.max()
    print arr.mean()
    print arr.min()
    # exit()

    # jobs = workload
    # steps = dict()
    # for s, v in placement_stats.iteritems():
    #     steps[int(float(s))] = s
    # steps = sorted(steps.iteritems(), key=lambda t: t[0], reverse=False)
    # x = np.array(steps)
    #
    # ordered_jobs = []
    # for job in jobs:
    #     ordered_jobs.append(int(job))
    # ordered_jobs = sorted(ordered_jobs)
    #
    # running_job = dict()
    # running_time = dict()
    # num_used_gpus = dict()
    # num_requested_gpus = dict()
    #
    # steps2 = np.zeros(int(window_max), dtype=np.int)
    # for step in range(int(window_max)):
    #     running_time[step] = dict()
    #
    # added = list()
    # for step, k in enumerate(steps):
    #     k_str = k[1]
    #     k = k[0]
    #     if k_str not in placement_stats:
    #         continue
    #
    #     # for jid in placement_stats[k_str]:
    #     for jid in ordered_jobs:
    #         jid = str(jid)
    #
    #         if jid in placement_stats[k_str]:
    #             submitted = float(placement_stats[k_str][jid]["submitted_time"])
    #             start = float(placement_stats[k_str][jid]["start_time"])
    #             if placement_stats[k_str][jid]["end_time"] is not None:
    #                 end = float(placement_stats[k_str][jid]["end_time"])
    #             else:
    #                 end = 0
    #             gpus_list = placement_stats[k_str][jid]["gpus"]
    #             arrival_time = workload[str(jid)]["arrival"]
    #
    #             if (k >= arrival_time) and (k <= start):
    #                 if k in num_requested_gpus:
    #                     num_requested_gpus[step] += len(gpus_list)
    #                 else:
    #                     num_requested_gpus[step] = len(gpus_list)
    #
    #             if (k >= start) and (k <= end):
    #                 if k in num_requested_gpus:
    #                     num_used_gpus[step] += len(gpus_list)
    #                 else:
    #                     num_used_gpus[step] = len(gpus_list)
    #
    #             if jid not in running_job:
    #                 running_job[jid] = np.zeros(len(steps2), dtype=np.int)
    #
    #             for i in range(int(start), int(end)):
    #                 running_job[jid][i] = len(gpus_list)
    #                 if jid not in running_time[i]:
    #                     running_time[i] = dict()
    #                 running_time[i][jid] = len(gpus_list)
    #
    # # accumulate running gpus to plot stepped figure
    # arunning = copy.deepcopy(running_job)
    # for step, k_str in enumerate(steps2):
    #     # k_str = str(k_str)
    #     for m, i in enumerate(ordered_jobs):
    #         jid = str(i)
    #         if jid in running_time[step]:
    #             for n, j in enumerate(ordered_jobs):
    #                 # if n >= m:
    #                 #     break
    #                 # j2id = str(j)
    #                 if jid != j:
    #                     if j in running_time[step]:
    #                         arunning[jid][step] += running_job[str(j)][step]
    #
    # from pprint import pprint
    #
    # df = pd.DataFrame(arunning)
    # ax = df.plot(kind='area', linewidth=0.0, legend=False)
    # for i, j in arunning.iteritems():
    #     print i, np.array(j).max()
    # # pprint(arunning)
    # # x = list()
    # # y = list()
    # # num_requested_gpus = sorted(num_requested_gpus.iteritems(), key=lambda t: t[0], reverse=False)
    # # for i, j in num_requested_gpus:
    # #     x.append(i)
    # #     y.append(j)
    # # # sns.tsplot(y)
    # # # df = pd.DataFrame(num_requested_gpus)
    # # # ax = df.plot(kind='area', linewidth=0.0, legend=False)
    # # fig_size = (13, 10)
    # # fig, ax = plt.subplots(1, 1, figsize=fig_size)
    # # plt.plot(x, y, color='g')
    # #
    # # num_used_gpus = sorted(num_used_gpus.iteritems(), key=lambda t: t[0], reverse=False)
    # # for i, j in num_used_gpus:
    # #     x.append(i)
    # #     y.append(j)
    # # plt.plot(x, y, color='b')
    #
    # # ax.fill_between(x, y, color='g', alpha=0.5)
    # ax.set_ylabel('# Requested GPUs', alpha=0.8, fontsize=34)
    # ax.set_xlabel('Time(s)', alpha=0.8, fontsize=34)
    # # ax.set_xlim([-1, 1000])
    # # ax.tick_params(labelsize=32, labelcolor="#404040")
    # # ax.legend(prop={'size': 28}, loc="lower right")
    # plt.show()
    # break
    #
    #

# fig_size = (30, 10)
# fig, axs = plt.subplots(1, 3, figsize=fig_size)
#
# data = stats.binom.rvs(n=3,  # Number workload type
#                        p=0.1,  # Probability of the big number
#                        size=10000)  # Number of trials
#
# # print(pd.crosstab(index="counts", columns=data))
# #
# pd.DataFrame(data).hist(range=(-0.5, 10.5), bins=11, ax=axs[0])
#
# data = stats.binom.rvs(n=2,  # Number workload type
#                        p=0.38,  # Probability of the big number
#                        size=10000)  # Number of trials
# axs[0].set_ylabel('Density', alpha=0.8, fontsize=48)
# axs[0].set_xlabel('Batch Size', alpha=0.8, fontsize=48)
# axs[0].tick_params(labelsize=42, labelcolor="#404040")
# axs[0].set_title("")
# axs[0].set_xlim([-2, 5])
# axs[0].set_ylim([0, 8000])
# # axs[0].legend(prop={'size': 28}, loc="lower right")
#
# # print(pd.crosstab(index="counts", columns=data))
# #
# pd.DataFrame(data).hist(range=(-0.5, 10.5), bins=11, ax=axs[1])
# axs[1].set_ylabel('Density', alpha=0.8, fontsize=42)
# axs[1].set_xlabel('Number of GPUs', alpha=0.8, fontsize=48)
# axs[1].tick_params(labelsize=42, labelcolor="#404040")
# axs[1].set_title("")
# axs[1].set_xlim([-2, 5])
# axs[1].set_ylim([0, 8000])
# # axs[1].legend(prop={'size': 28}, loc="lower right")
#
# data = stats.binom.rvs(n=2,  # Number workload type
#                        p=0.2,  # Probability of the big number
#                        size=10000)  # Number of trials
# pd.DataFrame(data).hist(range=(-0.5, 10.5), bins=11, ax=axs[2])
# axs[2].set_ylabel('Density', alpha=0.8, fontsize=42)
# axs[2].set_xlabel('Workload Type', alpha=0.8, fontsize=48)
# axs[2].tick_params(labelsize=42, labelcolor="#404040")
# axs[2].set_title("")
# axs[2].set_xlim([-2, 5])
# axs[2].set_ylim([0, 8000])
# # axs[2].legend(prop={'size': 28}, loc="lower right")
#
# folder = "/home/mamaral/Documents/2017/writing papers/SC17/images/scheduling/"
# if not os.path.exists(folder):
#     os.makedirs(folder)
# plt.savefig(folder + "work_dist.pdf", bbox_inches='tight')