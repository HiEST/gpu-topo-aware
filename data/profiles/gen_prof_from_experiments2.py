#!/usr/bin/python

import json
import numpy as np

from pprint import pprint
import matplotlib.pyplot as plt

from collections import OrderedDict


def init_prof(jobtypes1, jobtypes2, sizes):
    execution_time = dict()
    execution_time["solo"] = dict()
    execution_time["collocation"] = dict()

    # Create solo
    for type in jobtypes2:
        execution_time["solo"][type] = dict()
        for size in sizes:
            execution_time["solo"][type][size] = dict()
            execution_time["solo"][type][size]["num_gpus"] = dict()
            tmp = execution_time["solo"][type][size]["num_gpus"]
            for i in range(1, 4):
                tmp[i] = dict()
                tmp[i]["intra-socket"] = 0
                tmp[i]["inter-socket"] = 0

    # Create collocation in intra-domain
    for type1 in jobtypes1:
        execution_time["collocation"][type1] = dict()
        for size1 in sizes:
            execution_time["collocation"][type1][size1] = dict()
            execution_time["collocation"][type1][size1]["num_gpus"] = dict()
            tmp = execution_time["collocation"][type1][size1]["num_gpus"]

            for i in range(1, 4):
                tmp[i] = dict()
                for type2 in jobtypes2:
                    tmp[i][type2] = dict()
                    for size2 in sizes:
                        tmp[i][type2][size2] = dict()
                        tmp[i][type2][size2]["num_gpus"] = dict()
                        if i == 1:
                            tmp[i][type2][size2]["num_gpus"][3] = 0
                            tmp[i][type2][size2]["num_gpus"][1] = 0
                        elif i == 3:
                            tmp[i][type2][size2]["num_gpus"][1] = 0
                        elif i == 2:
                            tmp[i][type2][size2]["num_gpus"][2] = 0

    return execution_time


def remove_outliers(array):
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


# def init_prof(execution_time, jobtypes1, jobtypes2, sizes):
def fill_profile(jobtypes1, jobtypes2, sizes, folder, execution_time):
    name = str(folder + "/" + "results.csv").strip()

    with open(name) as f:
        for line in f:
            l = line.split(";")
            # print l
            if "solo" in l[0]:
                job_type = str(l[2])
                if job_type in jobtypes2:
                    gpus = str(l[4])
                    num_gpus = str(len(gpus.split(",")))
                    size = str(l[6])
                    array = list()
                    for i in range(13, len(l)):
                        value = float(str(l[i]).replace("\n", ""))
                        array.append(value)
                    array = np.array(array)
                    time = 0.0
                    if len(array) > 0:
                        time = array.mean()
                    place = "inter-socket"
                    if ("0,1" in gpus) or ("2,3" in gpus) or (len(gpus) <= 1):
                        place = "intra-socket"
                    if execution_time["solo"][job_type][size]["num_gpus"][num_gpus][place] <= 0:
                        execution_time["solo"][job_type][size]["num_gpus"][num_gpus][place] = time

            """
               Note that the collocation represent the time of the first application collocated with the second
               application.
               The application with "collocation" that is running in the same machine, but in isolation, that is
               each application running in different socket, has the exec time as running solo.
            """
            if "collocation" in l[0]:
                job_type1 = str(l[2])
                num_gpus1 = str(len(str(l[4]).split(",")))
                size1 = str(l[6])
                job_type2 = str(l[8])
                num_gpus2 = str(len(str(l[10]).split(",")))
                size2 = str(l[12]).replace("\n", "")
                if (job_type1 in jobtypes2) and (job_type2 in jobtypes2):
                    array = list()
                    for i in range(13, len(l)):
                        value = float(str(l[i]).replace("\n", ""))
                        array.append(value)
                    array = np.array(array)
                    time = 0.0
                    if len(array) > 0:
                        time = float(array.mean())
                    else:
                        if "1" in num_gpus1:
                            time = execution_time["solo"][job_type1][size1]["num_gpus"][num_gpus1]
                            
                    # print "job", job_type1, "size", size1, "numgpus", num_gpus1, "job2", job_type2, "size2", size2, \
                    #     "numgpus2", num_gpus2, time
                    if "1" in num_gpus1:
                        prof = execution_time["collocation"][job_type1][size1]["num_gpus"][num_gpus1][job_type2][size2
                        ]["num_gpus"]
                        for i in range(1, 4):
                            if i in prof:
                                if prof[str(i)] <= 0:
                                    prof[str(i)] = time
                        continue
                    if execution_time["collocation"][job_type1][size1]["num_gpus"][num_gpus1][job_type2][size2
                        ]["num_gpus"][num_gpus2] <= 0:
                        execution_time["collocation"][job_type1][size1]["num_gpus"][num_gpus1][job_type2][size2
                            ]["num_gpus"][num_gpus2] = time

    return execution_time


if __name__ == '__main__':
    folders = list()
    folders.append(
        "/home/mamaral/power8/multi-gpus/minsky/minsky-results/varying-gpu-number/results/parsed-results/")

    caffe_types1 = ["bvlc_alexnet", "bvlc_googlenet"]
    # caffe_types2 = ["bvlc_alexnet", "bvlc_googlenet", "bvlc_reference_caffenet"]
    caffe_types2 = ["bvlc_alexnet", "bvlc_googlenet"]
    # lammps = ["eam", "lj", "rhodo"]
    # sizes = ["tiny", "small", "default", "big"]
    sizes = ["1", "4", "64", "128"]

    with open("prof_from_experiments_full.json", "r") as out:
        execution_time = json.load(out)

    for folder in folders:
        execution_time = fill_profile(caffe_types1, caffe_types2, sizes, folder, execution_time)
        pprint(execution_time)

    with open("prof_from_experiments.json", "w") as out:
        json.dump(execution_time, out, sort_keys=True, indent=2, separators=(',', ':'))

