#!/usr/bin/python
import os
import glob
import numpy as np
import seaborn as sns

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from pprint import pprint
from collections import OrderedDict
from collections import defaultdict


def remove_outliers(array):
    print "///////////////////////////// REMOVE"
    print array
    if len(array) > 10:
        num = int(len(array) * 0.05)
        if num < 0:
            if len(array) > 10:
                num = 4
            elif len(array) > 6:
                num = 2
            else:
                num = 1
        a = array.tolist()
        for i in range(num):
            a = array.tolist()
            if len(array) > 3:
                a.remove(array.min())
                a.remove(array.max())
                array = np.array(a)
        a = array.tolist()
        for element in array:
            if element == 0:
                if len(a) > 1:
                    a.remove(element)
            array = np.array(a)

        print array
    return array


def get_links_traffic(file_name):
    times = list()
    link0rx = list()
    link1rx = list()
    link2rx = list()
    link3rx = list()
    link0tx = list()
    link1tx = list()
    link2tx = list()
    link3tx = list()

    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st

    count = 0
    try:
        with open(file_name) as f:
            # ['Link', '0:', 'Rx0:', '0', 'KBytes,', 'Tx0:', '0', 'KBytes']
            for line in f:
                l = str(line).split()
                if "elapsed" in line:
                    times.append(float(l[3]))
                else:
                    count += 1

                    if "0" in l[1]:
                        link0rx.append(int(l[3]))
                        link0tx.append(int(l[6]))
                    elif "1" in l[1]:
                        link1rx.append(int(l[3]))
                        link1tx.append(int(l[6]))
                    elif "2" in l[1]:
                        link2rx.append(int(l[3]))
                        link2tx.append(int(l[6]))
                    elif "3" in l[1]:
                        link3rx.append(int(l[3]))
                        link3tx.append(int(l[6]))
    except:
        print "Could not open file: " + file_name

    return link0rx, link1rx, link2rx, link3rx, link0tx, link1tx, link2tx, link3tx, times


def get_links_bandwidth_bidirectional(file_name):
    times = list()
    link0 = list()
    link1 = list()
    link2 = list()
    link3 = list()

    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st

    count = 0
    try:
        with open(file_name) as f:
            # ['Link', '0:', 'Rx0:', '0', 'KBytes,', 'Tx0:', '0', 'KBytes']
            for line in f:
                l = str(line).split()
                if "elapsed" in line:
                    times.append(float(l[3]))
                else:
                    count += 1
                    kb = int(l[3]) + int(l[6])

                    if "0" in l[1]:
                        link0.append(kb)
                    elif "1" in l[1]:
                        link1.append(kb)
                    elif "2" in l[1]:
                        link2.append(kb)
                    elif "3" in l[1]:
                        link3.append(kb)
    except:
        print "Could not open file: " + file_name

    return link0, link1, link2, link3, times


def get_links_traffic_bidirectional(folder, gpu):
    nvfile = folder + "/nvlink/gpu-" + str(gpu)
    link0, link1, link2, link3, times = get_links_bandwidth_bidirectional(nvfile)

    return link0, link1, link2, link3, times


def get_links_band(folder, gpu):
    interval = 5.0
    gb = (1024 * 1024)
    band0rx = list()
    band1rx = list()
    band2rx = list()
    band3rx = list()
    band0tx = list()
    band1tx = list()
    band2tx = list()
    band3tx = list()
    band_times = list()

    nvfile = folder + "/nvlink/gpu-" + str(gpu)
    link0rx, link1rx, link2rx, link3rx, link0tx, link1tx, link2tx, link3tx, times = get_links_traffic(nvfile)

    print len(link0rx), len(link1rx), len(link2rx), len(link3rx), len(link1tx), len(link2tx), len(link3tx), len(times)
    # n = min(len(link0rx), len(link1rx), len(link2rx), len(link3rx), len(link1tx), len(link2tx), len(link3tx), len(times))
    n = len(times)
    value = link0rx[0]
    for i in range(1, n):
        delta = (link0rx[i] - value) / interval
        value = link0rx[i]
        if delta < 0:
            delta = 0
        band0rx.append(delta / gb)

    value = link1rx[0]
    for i in range(1, n):
        delta = (link1rx[i] - value) / interval
        value = link1rx[i]
        if delta < 0:
            delta = 0
        band1rx.append(delta / gb)

    value = link2rx[0]
    for i in range(1, n):
        delta = (link2rx[i] - value) / interval
        value = link2rx[i]
        if delta < 0:
            delta = 0
        band2rx.append(delta / gb)

    value = link3rx[0]
    for i in range(1, n):
        delta = (link3rx[i] - value) / interval
        value = link3rx[i]
        if delta < 0:
            delta = 0
        band3rx.append(delta / gb)

    value = link0tx[0]
    for i in range(1, n):
        delta = (link0tx[i] - value) / interval
        value = link0tx[i]
        if delta < 0:
            delta = 0
        band0tx.append(delta / gb)

    value = link1tx[0]
    for i in range(1, n):
        delta = (link1tx[i] - value) / interval
        value = link1tx[i]
        if delta < 0:
            delta = 0
        band1tx.append(delta / gb)

    value = link2tx[0]
    for i in range(1, n):
        delta = (link2tx[i] - value) / interval
        value = link2tx[i]
        if delta < 0:
            delta = 0
        band2tx.append(delta / gb)

    value = link3tx[0]
    for i in range(1, n):
        delta = (link3tx[i] - value) / interval
        value = link3tx[i]
        if delta < 0:
            delta = 0
        band3tx.append(delta / gb)
        band_times.append(times[i])

    return band0rx, band1rx, band2rx, band3rx, band0tx, band1tx, band2tx, band3tx, band_times


# def get_traffic(folder, gpu):
#     file_name = folder + "/nvlink/gpu-" + str(gpu)
#     g1_link0, g1_link1, g1_link2, g1_link3, times = get_links_bandwidth_bidirectional(file_name)
#     host_gpu = list()
#     p2p = list()
#     for i, _ in enumerate(g1_link0):
#         host_gpu.append(g1_link2[i] + g1_link3[i])
#         p2p.append(g1_link0[i] + g1_link1[i])
#
#     return host_gpu, p2p, times
def get_traffic(folder, gpu):
    cpu = list()
    p2p = list()

    nvfile = folder + "/nvlink/gpu-" + str(gpu)
    link0rx, link1rx, link2rx, link3rx, link0tx, link1tx, link2tx, link3tx, times = get_links_traffic(nvfile)

    for i, _ in enumerate(times):
        if int(gpu) % 2 == 0:
            cpu.append(link2rx[i] + link2tx[i] + link3rx[i] + link3tx[i])
            p2p.append(link0rx[i] + link0tx[i] + link1rx[i] + link1tx[i])
        else:
            cpu.append(link0rx[i] + link0tx[i] + link1rx[i] + link1tx[i])
            p2p.append(link2rx[i] + link2tx[i] + link3rx[i] + link3tx[i])

    return cpu, p2p, times


def get_bandwidth(folder, percentage=True):
    # TODO: it should not be hard coded
    interval = 5.0
    gb = (1024 * 1024)
    cpu0_gpu0, g0_g1, times = get_traffic(folder, 0)
    cpu0_gpu1, g1_g0, _ = get_traffic(folder, 1)

    cpu1_gpu2, g2_g3, _ = get_traffic(folder, 2)
    cpu1_gpu3, g3_g2, _ = get_traffic(folder, 3)

    tt_cpu0_gpus = list()
    tt_cpu1_gpus = list()
    tt_gpu0_gpu1 = list()
    tt_gpu2_gpu3 = list()

    n = min(len(cpu0_gpu0), len(cpu0_gpu1), len(cpu1_gpu2), len(cpu1_gpu3), len(times))
    for i in range(n):
        tt_cpu0_gpus.append(cpu0_gpu0[i] + cpu0_gpu1[i])
        tt_cpu1_gpus.append(cpu1_gpu2[i] + cpu1_gpu3[i])
        tt_gpu0_gpu1.append((g0_g1[i] + g1_g0[i])/2)
        tt_gpu2_gpu3.append((g2_g3[i] + g3_g2[i])/2)

    times_band = list()
    cpu0_gpus_band = list()
    cpu1_gpus_band = list()
    gpu0_gpu1_band = list()
    gpu2_gpu3_band = list()

    value = tt_cpu0_gpus[0]
    for i in range(1, n):
        delta = (tt_cpu0_gpus[i] - value) / interval
        value = tt_cpu0_gpus[i]
        if delta < 0:
            delta = 0
        cpu0_gpus_band.append(delta/gb)

    value = tt_cpu1_gpus[0]
    for i in range(1, n):
        delta = (tt_cpu1_gpus[i] - value) / interval
        value = tt_cpu1_gpus[i]
        if delta < 0:
            delta = 0
        cpu1_gpus_band.append(delta/gb)

    value = tt_gpu0_gpu1[0]
    for i in range(1, n):
        delta = (tt_gpu0_gpu1[i] - value) / interval
        value = tt_gpu0_gpu1[i]
        if delta < 0:
            delta = 0
        gpu0_gpu1_band.append(delta / gb)

    for i in range(0, n-1):
        delta = (tt_gpu2_gpu3[i] - value) / interval
        value = tt_gpu2_gpu3[i]
        if delta < 0:
            delta = 0
        gpu2_gpu3_band.append(delta / gb)
        times_band.append(times[i])

    return cpu0_gpus_band, cpu1_gpus_band, gpu0_gpu1_band, gpu2_gpu3_band, times_band


if __name__ == '__main__':
    sns.set_context("paper", font_scale=1.5)
    ylim = 0
    fignum = -1
    array_length = 0

    # for algo in ["bf", "fcfs", "utilityaware-policy-neutral-postponed-False",
    for algo in ["bf", "utilityaware-policy-neutral-postponed-True"]:
        file_name = "../../../results/workloads-5/31-03-17--18-22-06-real/algo-" + \
                    algo + "/logs/"

        print file_name

        series = []

        cpu0_gpus_band, cpu1_gpus_band, gpu0_gpu1_band, gpu2_gpu3_band, x = get_bandwidth(file_name)
        print len(cpu0_gpus_band), len(cpu1_gpus_band), len(gpu0_gpu1_band), len(gpu2_gpu3_band), len(x)

        if len(cpu0_gpus_band) > 0:
            fig, ax = plt.subplots(1, 1)
            # print data
            ax = sns.tsplot(time=x, data=cpu0_gpus_band, condition="cpu0<->GPUS", color="g", linestyle=":")
            ax = sns.tsplot(time=x, data=cpu1_gpus_band, condition="cpu1<->GPUS", color="y", linestyle="-.")
            ax = sns.tsplot(time=x, data=gpu0_gpu1_band, condition="GPU0<->GPU1", color="b", linestyle="--")
            ax = sns.tsplot(time=x, data=gpu2_gpu3_band, condition="GPU2<->GPU3", color="r", linestyle="-")

            ax.set_xticks(x)
            ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(20))

            ax.grid()
            ax.set_xlabel('Time (s)', alpha=0.8)
            # ax.set_ylabel('NVLink bandwidth (GB/s)', alpha=0.8)
            ax.set_ylabel('NVLink links usage (%)', alpha=0.8)
            ax.set_title(algo)
            ax.grid()
            plt.legend(prop={'size': 13}, loc="upper left")

        #
        # folde_plot_tmp =  folde_plot + "/memory-bandwidth/"
        # if not os.path.exists(folde_plot_tmp):
        #     os.makedirs(folde_plot_tmp)
        # plt.savefig(folde_plot_tmp + '/memory-bandwidth-' + label + ".pdf", bbox_inches='tight')

        # for i in range(4):
        #     fig, ax = plt.subplots(4, 1)
        #     band0rx, band1rx, band2rx, band3rx, band0tx, band1tx, band2tx, band3tx, x =\
        #         get_links_band(file_name, i)
        #
        #     print len(x), len(band0rx)
        #     sns.tsplot(time=x, data=band0rx, condition="link0rx", color="k", alpha=0.6, linestyle="--", ax=ax[0])
        #     sns.tsplot(time=x, data=band0tx, condition="link0tx", color="r", alpha=0.6, linestyle=":", ax=ax[0])
        #     ax[0].set_xticklabels([])
        #
        #     sns.tsplot(time=x, data=band1rx, condition="link1rx", color="k", alpha=0.6, linestyle="--", ax=ax[1])
        #     sns.tsplot(time=x, data=band1tx, condition="link1tx", color="r", alpha=0.6, linestyle=":", ax=ax[1])
        #     ax[1].set_xticklabels([])
        #
        #     sns.tsplot(time=x, data=band2rx, condition="link2rx", color="k", alpha=0.6, linestyle="--", ax=ax[2])
        #     sns.tsplot(time=x, data=band2tx, condition="link2tx", color="r", alpha=0.6, linestyle=":", ax=ax[2])
        #     ax[2].set_xticklabels([])
        #
        #     sns.tsplot(time=x, data=band3rx, condition="link3rx", color="k", alpha=0.6, linestyle="--", ax=ax[3])
        #     sns.tsplot(time=x, data=band3tx, condition="link3tx", color="r", alpha=0.6, linestyle=":", ax=ax[3])
        #     ax[0].set_title(algo + "-GPU"+str(i))

    plt.show()
