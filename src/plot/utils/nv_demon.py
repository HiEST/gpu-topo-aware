#!/usr/bin/python

import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def get_gpu_utilization(file_name):
    gpu0 = list()
    gpu1 = list()
    gpu2 = list()
    gpu3 = list()
    times = list()

    try:
        with open(file_name + 'dmon.out') as f:
            for line in f:
                if "#" not in line:
                    l = str(line).split()
                    if "elapsed" in line:
                        times.append(float(l[3]))
                    else:
                        value = int(l[3])
                        if "0" in l[0]:
                            gpu0.append(value)
                        elif "1" in l[0]:
                            gpu1.append(value)
                        elif "2" in l[0]:
                            gpu2.append(value)
                        elif "3" in l[0]:
                            gpu3.append(value)
    except:
        print "Could not open file: " + file_name

    return gpu0, gpu1, gpu2, gpu3, times


def get_mem_utilization(file_name):
    mem0 = list()
    mem1 = list()
    mem2 = list()
    mem3 = list()
    times = list()

    try:
        with open(file_name + 'dmon.out') as f:
            for line in f:
                if "#" not in line:
                    l = str(line).split()
                    if "elapsed" in line:
                        times.append(float(l[3]))
                    else:
                        value = int(l[4])
                        if "0" in l[0]:
                            mem0.append(value)
                        elif "1" in l[0]:
                            mem1.append(value)
                        elif "2" in l[0]:
                            mem2.append(value)
                        elif "3" in l[0]:
                            mem3.append(value)
    except:
        print "Could not open file: " + file_name

    return mem0, mem1, mem2, mem3, times


def get_avg_gpu_utilization(file_name):
    gpu0, gpu1, gpu2, gpu3, times = get_gpu_utilization(file_name)
    average_gpu_utilization = list()
    for i, _ in enumerate(gpu0):
        value = 0
        if i < len(gpu0):
            value += gpu0[i]
        if i < len(gpu1):
            value += gpu1[i]
        if i < len(gpu2):
            value += gpu2[i]
        if i < len(gpu3):
            value += gpu3[i]
        value /= 4*100.0
        average_gpu_utilization.append(value)
    return average_gpu_utilization, times


def get_avg_gpu_mem_utilization(file_name):
    mem0, mem1, mem2, mem3, times = get_mem_utilization(file_name)
    average_mem_utilization = list()
    for i, _ in enumerate(mem0):
        value = 0
        if i < len(mem0):
            value += mem0[i]
        if i < len(mem1):
            value += mem1[i]
        if i < len(mem2):
            value += mem2[i]
        if i < len(mem3):
            value += mem3[i]
        value /= 4*100.0
        average_mem_utilization.append(value)
    return average_mem_utilization, times


if __name__ == '__main__':
    sns.set_context("paper", font_scale=1.5)

    # sizes = ["1", "4", "64", "128"]
    sizes = ["64"]
    # gpuset = ["0", "0,1", "0,2", "1,2,3"]
    gpuset = ["0"]
    gpusetname= {"0": "0", "0,1": "0-1", "0,2": "0-2", "1,2,3": "1-2-3"}
    # applications = ["bvlc_alexnet", "bvlc_googlenet", "bvlc_reference_caffenet"]
    applications = ["bvlc_alexnet"]
    fancyName = {"bvlc_alexnet": "AlexNet", "bvlc_googlenet": "GoogLeNet"}
    folder = "/home/mamaral/power8/multi-gpus/minsky/minsky-results/varying-gpu-number/results"


    placement = "solo"

    for app in applications:
        for size in sizes:
            for gpus in gpuset:
                ylim = 0
                fignum = -1
                array_length = 0

                for algo in ["bf", "fcfs", "utilityaware-policy-neutral-postponed-False",
                             "utilityaware-policy-neutral-postponed-True"]:
                    file_name = "../../../results/workloads-5/31-03-17--18-22-06-real/algo-" + \
                                algo + "/logs/"

                    print file_name
                    average_gpu_utilization = get_avg_gpu_utilization(file_name)
                    average_mem_utilization = get_avg_gpu_mem_utilization(file_name)

                    fig, ax = plt.subplots(1, 1)

                        # print data
                        # x = [i * 5 for i in range(len(gpu0))]
                        # ax = sns.tsplot(time=x, data=gpu0, condition="gpu0", color="g", linestyle="--")
                        # x = [i * 5 for i in range(len(gpu1))]
                        # ax = sns.tsplot(time=x, data=gpu1, condition="gpu1", color="b", linestyle="--")
                        # x = [i * 5 for i in range(len(gpu2))]
                        # ax = sns.tsplot(time=x, data=gpu2, condition="gpu2", color="r", linestyle="-.")
                        # x = [i * 5 for i in range(len(gpu3))]
                        # ax = sns.tsplot(time=x, data=gpu3, condition="gpu3", color="k", linestyle=":")

                    if len(average_gpu_utilization) > 0:
                        x = [i * 5 for i in range(len(average_gpu_utilization))]
                        ax = sns.tsplot(time=x, data=average_gpu_utilization, condition="Computing", color="b", linestyle="--")

                    if len(average_gpu_utilization) > 0:
                        x = [i * 5 for i in range(len(average_mem_utilization))]
                        ax = sns.tsplot(time=x, data=average_mem_utilization, condition="Memory Footprint", color="r", linestyle=":")

                    ax.set_xticks(x)
                    x_ticket = int(size)
                    if x_ticket == 1:
                        x_ticket = 4

                    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(x_ticket))
                    ax.grid()
                    ax.set_xlabel('Time (s)', alpha=0.8)
                    ax.set_ylabel('GPU Utilization (%)', alpha=0.8)
                    ax.set_title(algo)
                    ax.grid()
                    plt.legend(prop={'size': 13}, loc="lower right")


                    # folde_plot_tmp =  folde_plot + "/memory-bandwidth/"
                    # if not os.path.exists(folde_plot_tmp):
                    #     os.makedirs(folde_plot_tmp)
                    # plt.savefig(folde_plot_tmp + '/memory-bandwidth-' + label + ".pdf", bbox_inches='tight')

        plt.show()