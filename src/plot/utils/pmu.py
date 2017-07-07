#!/usr/bin/python
import os
import numpy as np
import seaborn as sns

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def get_mem_band_array(file_name):
    membandwidth = list()
    cachel2bandwidth = list()
    cacheL3Bandwidth = list()
    totalcachebandwidth = list()
    totall3misses = list()

    l1froml2 = list()
    l1froml3 = list()
    l1froml4 = list()
    l1frommem = list()
    l3frommem = list()
    l3tomem = list()

    l4 = 0
    l3 = 0
    mem = 0
    try:
        with open(file_name) as f:
            for line in f:
                l = line.split()
                if len(l) > 2:
                    value = l[1].replace(".", "").replace("\n", "")
                    if "MISS" in l:
                        value = float(value) / 1000
                    else:
                        value = float(value) * 128.0

                    if "PM_DATA_ALL_FROM_L2" in l:
                        l1froml2.append(value)
                    elif "PM_DATA_ALL_FROM_L3" in l:
                        l1froml3.append(value)
                    elif "PM_L3_CO_MEM" in l:
                        l3tomem.append(value)
                    elif ("PM_L3_ST_PREF" in l) or ("PM_L3_LD_PREF" in l):
                        l3 += value
                    elif ("PM_DATA_ALL_FROM_LL4" in l) or ("PM_DATA_ALL_FROM_RL4" in l) or (
                        "PM_DATA_ALL_FROM_DL4" in l):
                        l4 += value
                    elif ("PM_DATA_ALL_FROM_LMEM" in l) or ("PM_DATA_ALL_FROM_RMEM" in l) or (
                        "PM_DATA_ALL_FROM_DMEM" in l):
                        mem += value
                    elif "PM_DATA_FROM_L3MISS" in l:  # The end of a cycle. This is the last pmu counter
                        totall3misses.append(value)
                        l3frommem.append(l3)
                        l1froml4.append(l4)
                        l1frommem.append(mem)
                        l4 = 0
                        l3 = 0
                        mem = 0

            # print "###### L1fromL3",  "NUM ", numThreads, " Values: ", L1fromL3
            # print "###### L1fromL4", " Values: ", len(l1froml4)
            # print "###### L1fromMEM", " Values: ", len(l1frommem)
            # print "###### L3fromMEM", " Values: ", len(l3frommem)
            # print "###### L3toMEM", " Values: ", len(l3tomem)

            ### Calculate the bandwidth per thread amount
            deltat = 5.0  # this is the time used to collect the counters
            gb = (1024 * 1024 * 1024.0)
            datumBand = 0
            datumCacheL2 = 0
            datumCacheL3 = 0
            datumTotal = 0
            numSamples = 0
            for i in range(len(l1frommem)):  # all the values has the same array size
                datumBand = ((l1frommem[i] + l3frommem[i] + l3tomem[i] + l1froml4[i]) / deltat) / gb
                membandwidth.append(datumBand)
                # print "###### PARCIAL", "Samples: ", numSamples, " Values: ", datumBand,
                datumCacheL2 = ((l1froml2[i] * deltat) * 8 + (datumCacheL2 * 2)) / 10
                cachel2bandwidth.append(datumCacheL2)
                datumCacheL3 += ((l1froml3[i] * deltat) * 8 + (datumCacheL3 * 2)) / 10
                cacheL3Bandwidth.append(datumCacheL3)
                datumTotal += ((((l1froml2[i] + l1froml3[i]) * deltat) * 8) + (datumTotal * 2)) / 10
                totalcachebandwidth.append(datumTotal)
    except:
        print "Could not open file: " + file_name

    return membandwidth, totall3misses


if __name__ == '__main__':
    sns.set_context("paper", font_scale=1.5)
    ylim = 0
    fignum = -1
    array_length = 0

    # for algo in ["bf", "fcfs", "utilityaware-policy-neutral-postponed-False", "utilityaware-policy-neutral-postponed-True"]:
    for algo in ["bf"]:
        file_name = "../../../results/workloads-5/30-03-17--10-10-02-real/algo-" + \
                    algo + "/logs/"

        # print file_name
        file_names = list()
        for root, directories, files in os.walk(file_name):
            if "job_id" in root and "metrics" in root:
                for file in files:
                    if "pmu" in file:
                        print file
                        file_names.append(root + "/" + file)

        fig, ax = plt.subplots(1, 1)
        for file_name in file_names:
            membandwidth, totall3misses = get_mem_band_array(file_name)

            if len(membandwidth) > 0:
                # print data
                x = [i * 5 for i in range(len(membandwidth))]
                ax = sns.tsplot(time=x, data=membandwidth, condition="HOST<->MEM", color="g", linestyle=":")

                ax.set_xticks(x)
                x_ticket = int(len(membandwidth))/10

                ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(20))

                ax.grid()
                ax.set_xlabel('Time (s)', alpha=0.8)
                # ax.set_ylabel('NVLink bandwidth (GB/s)', alpha=0.8)
                ax.set_ylabel('GB/s', alpha=0.8)
                ax.set_title(algo)
                ax.grid()
                plt.legend(prop={'size': 13}, loc="upper left")


                # folde_plot_tmp =  folde_plot + "/memory-bandwidth/"
                # if not os.path.exists(folde_plot_tmp):
                #     os.makedirs(folde_plot_tmp)
                # plt.savefig(folde_plot_tmp + '/memory-bandwidth-' + label + ".pdf", bbox_inches='tight')

    plt.show()