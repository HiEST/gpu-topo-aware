# from __future__ import division

import configparser


class Simulator:
    def __init__(self, config):

        self.length = config.getfloat("simulator", "length")
        self.period = config.getfloat("simulator", "period")
        self.digits = config.getint("simulator", "digits")
        self.sim_mode = config.getboolean("simulator", "enabled")

        self.curr_time = 0.0

    # Convert standard time in float format to discrete time in "step" format.
    def to_sim_time(self, t):
        s = t - (t % self.period)
        s = s + self.period if t % self.period != 0 else s
        return round(s, self.digits)

    # Generate list of time steps between the specified interval. Similar to
    # Python's range(), with float support.
    def step(self):
        """This function control the simulator time, where each time is a step"""
        # while self.curr_time <= self.length:
        while True:
            yield round(self.curr_time, self.digits)
            self.curr_time += self.period
