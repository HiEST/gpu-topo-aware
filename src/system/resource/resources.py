#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Keeps the list of resources in the cluster.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

import cluster


def create(config, num_machines):
    return Resources(config, num_machines)


class Resources:
    def __init__(self, config, num_machines):
        self.config = config
        self.cluster = cluster.Cluster(self.config, num_machines)
