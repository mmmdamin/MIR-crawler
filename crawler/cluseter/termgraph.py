# coding=utf-8
from __future__ import print_function
import argparse
import sys

tick = '▇'
sm_tick = '|'

width = 50
try:
    range = xrange
except NameError:
    pass


def main(labels, data):
    # determine type of graph

    # verify data
    m = len(labels)
    if m != len(data):
        print(">> Error: Label and data array sizes don't match")
        sys.exit(1)

    # massage data
    ## normalize for graph
    max = 0
    for i in range(m):
        if data[i] > max:
            max = data[i]

    step = max / width
    # display graph
    for i in range(m):
        print_blocks(labels[i], data[i], step)

    print()


def print_blocks(label, count, step):
    # TODO: add flag to hide data labels
    blocks = int(count / step)
    print("{}: ".format(label), end="")
    if count < step:
        sys.stdout.write(sm_tick)
    else:
        for i in range(blocks):
            sys.stdout.write(tick)

    print("{:>7.2f}".format(count))


def read_data(filename):
    # TODO: add verbose flag
    stdin = filename == '-'

    print("------------------------------------")
    print("Reading data from", ("stdin" if stdin else filename))
    print("------------------------------------\n")

    labels = []
    data = []

    f = sys.stdin if stdin else open(filename, "r")
    for line in f:
        line = line.strip()
        if line:
            if not line.startswith('#'):
                if line.find(",") > 0:
                    cols = line.split(',')
                else:
                    cols = line.split()
                labels.append(cols[0].strip())
                data_point = cols[1].strip()
                data.append(float(data_point))

    f.close()
    return labels, data
