import glob
import os


def module_search(path="."):
    if not os.path.exists(path):
        raise FileNotFoundError
    if not os.path.isdir(path):
        raise NotADirectoryError

    modules = []
    for filename in glob.glob(os.path.join(path, "**", "main.tf"), recursive=True):
        modules.append(os.path.dirname(filename))
    return modules
