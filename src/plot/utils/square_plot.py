#!/usr/bin/python

import numpy as np
import random
import seaborn as sns; sns.set()
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from matplotlib.ticker import AutoMinorLocator

plt.rcParams['ps.useafm'] = True
plt.rcParams['pdf.use14corefonts'] = True
plt.rcParams['text.usetex'] = True #Let TeX do the typsetting
plt.rcParams['font.family'] = 'Times New Roman' # ... for regular text

def generate_color():
    color = '#{:02x}{:02x}{:02x}'.format(*map(lambda x: random.randint(0, 255), range(3)))
    return color


def plot_square(ax, jobid, start_time, end_time, gpulist, pattern, color, legend=True):
    """     position        moving forward """
    """ (x_start, y_start),      (x, y)    """
    lower_gpu = np.array(gpulist).min() + 0.05
    num_gpus = len(gpulist) - 0.1
    end_time = end_time - start_time

    label = ""
    if legend:
        label = "J"+str(jobid)

    for p in [
        patches.Rectangle(
            (start_time, lower_gpu), end_time, num_gpus,
            hatch=pattern,
            facecolor=color,
            alpha=0.4,
            label=label,
        ),
    ]:
        ax.add_patch(p)

    # label = "J" + str(jobid)
    # ax.text(start_time + (end_time/2), lower_gpu + (num_gpus/2), label, fontsize=14,
    #         bbox={'facecolor':'white', 'alpha':0.5, 'pad':1})


def add_text(ax, xposition, yposition, label, fontsize, background=False):
    if background:
        ax.text(xposition, yposition, label, fontsize=fontsize,
                # bbox={'facecolor':'white', 'alpha':0.2, 'pad':1})
                bbox={'facecolor':'white', 'pad':1})
    else:
        ax.text(xposition, yposition, label, fontsize=fontsize)
    return ax


def add_job_square(ax, id, job, pattern, color):
    start_time = job['start_time']
    end_time = job['end_time']
    gpus = job['gpus']

    print "Job: ", id, " start: ", start_time, " end: ", end_time, " gpus: ", gpus

    label = True
    for gpu in gpus:
        plot_square(ax, id, int(start_time), int(end_time), [int(gpu)], pattern, color, label)
        label = False
    return ax


if __name__ == '__main__':
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    fig_size = (40, 10)
    fig, axs = plt.subplots(2, 1, figsize=fig_size)

    num_gpus = 4

    ax = axs[0]

    ax.set_ylim([0, num_gpus])
    ax.set_xlim([0, 450])

    jobs = dict()
    jobs[0] = dict()
    jobs[0]['submitted_time'] = 1.0021739006
    jobs[0]['start_time'] = 1.0021739006
    jobs[0]['end_time'] = 65.4728679657
    jobs[0]['gpus'] = ["2"]

    jobs[1] = dict()
    jobs[1]['submitted_time'] = 16.0388100147
    jobs[1]['start_time'] = 16.0388100147
    jobs[1]['end_time'] = 119.978269815
    jobs[1]['gpus'] = ["0"]

    jobs[2] = dict()
    jobs[2]['submitted_time'] = 25.0712928772
    jobs[2]['start_time'] = 25.0712928772
    jobs[2]['end_time'] = 124.009707928
    jobs[2]['gpus'] = ["3"]

    jobs[3] = dict()
    jobs[3]['submitted_time'] = 26.084225893
    jobs[3]['start_time'] = 66.4836959839
    jobs[3]['end_time'] = 258.143490791
    jobs[3]['gpus'] = ["1", "2"]

    jobs[4] = dict()
    jobs[4]['submitted_time'] = 30.1170678139
    jobs[4]['start_time'] = 125.017673016
    jobs[4]['end_time'] = 288.233713865
    jobs[4]['gpus'] = ["0", "3"]

    jobs[5] = dict()
    jobs[5]['submitted_time'] = 31.125289917
    jobs[5]['start_time'] = 259.151671886
    jobs[5]['end_time'] = 417.476558924
    jobs[5]['gpus'] = ["1", "2"]

    patterns = ['/', 'o', 'x', '-', '+', 'O', '.', '*']  # more patterns

    colors = ['#f2b1bc', '#02e0bd', '#7cc8f0', '#9083de', '#07a998', '#5a71ff', '#224fc2', '#19f2fb', '#8e9e1f', '#3266c8',
              '#2b2c08', '#975ce0', '#e1c295', '#95e4c9', '#5d160e', '#4b5241', '#7a55f8', '#ac3320', '#58aa2d', '#953164']
    """start_time, gpulist, end_time, pattern, color"""

    job = sorted(jobs.iteritems(), key=lambda t: t[1]['submitted_time'])
    previous_submitted_time = -1
    maxy = 0
    for id, job in jobs.iteritems():
        label = "J" + str(id)
        yposition = num_gpus
        if (job['submitted_time'] - previous_submitted_time) <= 2:
            yposition += 0.2
            maxy += 0.2
        ax = add_job_square(ax, id, job, patterns[id], colors[id])
        ax = add_text(ax, job['submitted_time'] - 2, yposition, label)
        previous_submitted_time = job['submitted_time']

    ax = add_text(ax, previous_submitted_time + 10, (num_gpus + (maxy/3)), "} Job Arrivals", background=False)

    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(6))
    # ax.set_xticklabels(ax.xaxis.get_majorticklabels(), rotation=90)
    ax.xaxis.set_ticklabels([], minor=False)

    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))

    ax.yaxis.set_ticklabels([0,1,2,3], minor=True)
    ax.yaxis.set_ticklabels([], minor=False)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=10, fancybox=True, shadow=True)
    ax.set_ylabel('GPU IDs')
    ax.xaxis.grid(True, which='minor')

    # plt.grid(which='minor')

    axs[1].set_ylim([0, num_gpus])
    axs[1].set_xlim([0, 450])
    axs[1].xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(6))
    for tick in axs[1].get_xticklabels():
        tick.set_rotation(45)


    plt.subplots_adjust(wspace=0, hspace=0.05)
    sns.set_style("ticks")
    plt.show()