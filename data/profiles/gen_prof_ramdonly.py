#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Generate a profile with random values for testing propose.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import json
import random
from pprint import pprint


def create_prof(execution_time, jobtypes1, jobtypes2, sizes):
    # Create solo
    for type in jobtypes1:
        execution_time["solo"]["inter"][type] = dict()
        execution_time["solo"]["intra"][type] = dict()
        for size in sizes:
            execution_time["solo"]["inter"][type][size] = dict()
            execution_time["solo"]["intra"][type][size] = dict()
            execution_time["solo"]["inter"][type][size]["num_gpus"] = dict()
            execution_time["solo"]["intra"][type][size]["num_gpus"] = dict()
            tmp1 = execution_time["solo"]["inter"][type][size]["num_gpus"]
            tmp2 = execution_time["solo"]["intra"][type][size]["num_gpus"]
            for i in range(1, 2, 3):
                tmp1[i] = dict()
                tmp2[i] = dict()

            # One GPU
            tmp1[1] = random.randint(200, 300)
            tmp2[1] = random.randint(400, 500)
            # Two GPUs
            tmp1[2] = random.randint(100, 230)
            tmp2[2] = random.randint(260, 360)
            # Three GPUs
            tmp1[3] = random.randint(80, 98)
            tmp2[3] = random.randint(200, 250)

    # Create collocation in intra-domain
    for type1 in jobtypes1:
        execution_time["collocation"]["inter"][type1] = dict()
        execution_time["collocation"]["intra"][type1] = dict()
        for size1 in sizes:
            execution_time["collocation"]["inter"][type1][size1] = dict()
            execution_time["collocation"]["intra"][type1][size1] = dict()
            for type2 in jobtypes2:
                execution_time["collocation"]["inter"][type1][size1][type2] = dict()
                execution_time["collocation"]["intra"][type1][size1][type2] = dict()
                for size2 in sizes:
                    execution_time["collocation"]["inter"][type1][size1][type2][size2] = dict()
                    execution_time["collocation"]["intra"][type1][size1][type2][size2] = dict()
                    execution_time["collocation"]["inter"][type1][size1][type2][size2]["num_gpus"] = dict()
                    execution_time["collocation"]["intra"][type1][size1][type2][size2]["num_gpus"] = dict()
                    tmp1 = execution_time["collocation"]["inter"][type1][size1][type2][size2]["num_gpus"]
                    tmp2 = execution_time["collocation"]["intra"][type1][size1][type2][size2]["num_gpus"]
                    for i in range(1, 2, 3):
                        tmp1[i] = dict()
                        tmp2[i] = dict()

                    # One GPU
                    tmp1[1] = random.randint(300, 400)
                    tmp2[1] = random.randint(500, 600)
                    # Two GPUs
                    tmp1[2] = random.randint(200, 330)
                    tmp2[2] = random.randint(360, 460)
                    # Three GPUs
                    tmp1[3] = random.randint(180, 198)
                    tmp2[3] = random.randint(300, 350)

    return execution_time

random.seed(1234)

caffe = ["googlenet", "alexnet", "caffenet"]
# lammps = ["eam", "lj", "rhodo"]
sizes = ["small", "default", "big", "tiny"]


execution_time = dict()
execution_time["collocation"] = dict()
execution_time["collocation"]["inter"] = dict()
execution_time["collocation"]["intra"] = dict()

execution_time["solo"] = dict()
execution_time["solo"]["inter"] = dict()
execution_time["solo"]["intra"] = dict()

execution_time = create_prof(execution_time, caffe, caffe, sizes)
# execution_time = create_prof(execution_time, lammps, lammps, sizes)
# execution_time = create_prof(execution_time, lammps, caffe, sizes)

pprint(execution_time)

with open("prof_from_experiments.json", "w") as out:
    json.dump(execution_time, out, sort_keys=True, indent=2, separators=(',', ':'))
