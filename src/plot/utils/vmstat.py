#!/usr/bin/python


def get_memory(file_name):
    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st
    memory_swpd = list()
    memory_free = list()
    memory_buff = list()
    memory_cache = list()
    swap_si = list()
    swap_so = list()
    io_bi = list()
    io_bo = list()
    system_sin = list()
    system_scs = list()
    cpu_us = list()
    cpu_sy = list()
    cpu_id = list()
    cpu_wa = list()
    cpu_st = list()

    try:
        with open(file_name) as f:
            for line in f:
                l = str(line).replace("\'", "").replace("\n", "").split(";")
                memory_swpd.append(int(l[2]))
                memory_free.append(int(l[3]))
                memory_buff.append(int(l[4]))
                memory_cache.append(int(l[5]))
                swap_si.append(int(l[6]))
                swap_so.append(int(l[7]))
                io_bi.append(int(l[8]))
                io_bo.append(int(l[9]))
                system_sin.append(int(l[10]))
                system_scs.append(int(l[11]))
                cpu_us.append(int(l[12]))
                cpu_sy.append(int(l[13]))
                cpu_id.append(int(l[14]))
                cpu_wa.append(int(l[15]))
                cpu_st.append(int(l[16]))
    except:
        print "Could not open file: " + file_name

    return


def get_memory(file_name):
    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st
    memory_swpd = list()
    memory_free = list()
    memory_buff = list()
    memory_cache = list()

    try:
        with open(file_name) as f:
            for line in f:
                l = str(line).replace("\'", "").replace("\n", "").split(";")
                memory_swpd.append(int(l[2]))
                memory_free.append(int(l[3]))
                memory_buff.append(int(l[4]))
                memory_cache.append(int(l[5]))

    except:
        print "Could not open file: " + file_name

    return memory_swpd, memory_free, memory_buff, memory_cache


def get_swap(file_name):
    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st
    swap_si = list()
    swap_so = list()

    try:
        with open(file_name) as f:
            for line in f:
                l = str(line).replace("\'", "").replace("\n", "").split(";")
                swap_si.append(int(l[6]))
                swap_so.append(int(l[7]))
    except:
        print "Could not open file: " + file_name

    return swap_si, swap_so


def get_io(file_name):
    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st
    io_bi = list()
    io_bo = list()

    try:
        with open(file_name) as f:
            for line in f:
                l = str(line).replace("\'", "").replace("\n", "").split(";")
                io_bi.append(int(l[8]))
                io_bo.append(int(l[9]))
    except:
        print "Could not open file: " + file_name

    return io_bi, io_bo


def get_cpu(file_name):
    # vmstat
    #procs - ----------memory - --------- ---swap - - -----io - --- -system - - ------cpu - ----
    # r;b;       swpd;free;buff;cache;       si;so;     bi;bo;    in;cs;        us;sy;id;wa;st
    cpu_us = list()
    cpu_sy = list()
    cpu_id = list()
    cpu_wa = list()
    cpu_st = list()

    try:
        with open(file_name) as f:
            for line in f:
                l = str(line).replace("\'", "").replace("\n", "").split(";")
                cpu_us.append(int(l[12]))
                cpu_sy.append(int(l[13]))
                cpu_id.append(int(l[14]))
                cpu_wa.append(int(l[15]))
                cpu_st.append(int(l[16]))
    except:
        print "Could not open file: " + file_name

    return cpu_us, cpu_sy, cpu_id, cpu_wa, cpu_st


import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

if __name__ == '__main__':
    sns.set_context("paper", font_scale=1.5)
    sns.set_style("whitegrid")
    sns.set_style("ticks")

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
                # for gpus in ["0-2", "1-3"]:

                # data_bandwidth = list()
                # data_L3_misses = list()
                array_length = 0
                # for run in range(1, 3):
                # solo/bvlc_alexnet/gpus-0/batch-size-1/run1/metrics

                for algo in ["bf", "fcfs", "utilityaware-policy-neutral-postponed-False", "utilityaware-policy-neutral-postponed-True"]:
                    file_name = "../../../results/workloads-5/31-03-17--18-22-06-real/algo-" + \
                                    algo + "/logs/vmstat-formatted.out"
                    cpu_us, cpu_sy, cpu_id, cpu_wa, cpu_st = get_cpu(file_name)

                    print cpu_us
                    if len(cpu_us) > 0:
                        fig, ax = plt.subplots(1, 1)
                        # print data
                        x = [i * 5 for i in range(len(cpu_sy))]
                        ax = sns.tsplot(time=x, data=cpu_us, condition="cpu_us", color="g", linestyle=":")
                        ax = sns.tsplot(time=x, data=cpu_sy, condition="cpu_sy", color="b", linestyle="--")

                        ax.set_xticks(x)
                        x_ticket = int(size)
                        if x_ticket == 1:
                            x_ticket = 4

                        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(x_ticket))
                        ax.grid()
                        ax.set_xlabel('Time (s)', alpha=0.8)
                        ax.set_ylabel('CPU usage (%)', alpha=0.8)
                        ax.set_title(algo)
                        plt.legend()


                        # folde_plot_tmp =  folde_plot + "/memory-bandwidth/"
                        # if not os.path.exists(folde_plot_tmp):
                        #     os.makedirs(folde_plot_tmp)
                        # plt.savefig(folde_plot_tmp + '/memory-bandwidth-' + label + ".pdf", bbox_inches='tight')

        plt.show()