#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# In order to execute a job, a thread is create to run the command in background.
# When the command finishes, it returns its output.
#
# Copyright © 2017 Marcelo Amaral <marcelo.amaral@bsc.es>

from __future__ import print_function
import time
import copy
import threading
import subprocess


def create_job(cmd, background=False):
    e = Executor(cmd,  background)
    try:
        e.start()
    except:
        e.set_state(True)
    return e


class Executor(threading.Thread):
    def __init__(self, cmd, background=False):
        threading.Thread.__init__(self)
        self.threadLock1 = threading.Lock()
        self.threadLock2 = threading.Lock()
        self.cmd = cmd
        self.background = background
        self.finished = False
        self.start_time = None
        self.finish_time = None

    def execute_background(self, cmd):
        subprocess.Popen(cmd)
        self.set_finish_time(time.time())
        self.set_state(True)

    def execute(self, cmd):
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            # TODO: this terminate phase should not be hardcoded
            if ('finished' in stdout_line) or (self.has_finished()):
                break
            yield stdout_line

        self.set_finish_time(time.time())
        self.set_state(True)
        popen.stdout.close()
        popen.kill()  # kill all child processes, such as the ones collecting metrics
        return

    def run(self):
        self.set_start_time(time.time())
        if not self.background:
            workload = self.execute(self.cmd)
            try:
                while not self.has_finished():
                    out = workload.next()
                    if out is None:
                        break
            except:
                print("The process has finished")
        else:
            self.execute_background(self.cmd)

    def has_finished(self):
        self.threadLock1.acquire()
        state = copy.deepcopy(self.finished)
        self.threadLock1.release()
        return state

    def set_state(self, state):
        self.threadLock1.acquire()
        self.finished = state
        self.threadLock1.release()

    def get_time(self):
        self.threadLock2.acquire()
        s = copy.deepcopy(self.start_time)
        f = copy.deepcopy(self.finish_time)
        self.threadLock2.release()
        if f is None:
            f = time.time()
        return f - s

    def set_start_time(self, t):
        self.threadLock2.acquire()
        self.start_time = t
        self.threadLock2.release()

    def set_finish_time(self, t):
        self.threadLock2.acquire()
        self.finish_time = t
        self.threadLock2.release()