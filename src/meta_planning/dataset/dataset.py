from ..parsers import parse_model, parse_trajectory

import os

learning_domains = ["blocks", "driverlog", "ferry", "floortile", "grid", "gripper", "hanoi", "miconic", "npuzzle", "parking", "rovers", "satellite", "transport", "visitall", "zenotravel"]
recognition_domains = [["nondet-blocks-A", "nondet-blocks-B", "nondet-blocks-C"]]

all_domains = learning_domains + [d for group in recognition_domains for d in group]

def list_domains():

    list_learning_domains()
    print()
    list_recognition_domains()


def list_learning_domains():
    print("Learning domains:")
    for d in learning_domains:
        print("\t %s" % d)


def list_recognition_domains():
    print("Recognition domains:")
    for i in range(len(recognition_domains)):
        print("\t Group %s: %s" % (i, ", ".join(recognition_domains[i])))



def load_model(domain, completeness="reference"):
    model_path = os.path.join(os.path.dirname(__file__), domain, completeness)

    return parse_model(model_path)


def load_trajectories(domain, select=range(10)):
    model_path = os.path.join(os.path.dirname(__file__), domain, "reference")

    M = parse_model(model_path)

    trajectory_files = ["trajectory-%s" % str(i).zfill(2) for i in select]
    trajectories = []

    for f in trajectory_files:
        trajectory_path = os.path.join(os.path.dirname(__file__), domain, f)

        trajectories += [parse_trajectory(trajectory_path, M)]


    return trajectories