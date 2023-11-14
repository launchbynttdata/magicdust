import os
from setuptools import setup, find_packages
import subprocess

VERSION = "1.0.1"


def install_requires():
    with open("requirements.txt") as f:
        packages = f.read()
    return packages.split("\n")


def get_version():
    version = None
    d = os.path.dirname(__file__)
    if os.path.isdir(os.path.join(d, ".git")):
        cmd = "git describe --tags".split()
        try:
            version = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            print("Unable to get git tag")
    if version:
        return version
    else:
        return VERSION


setup(
    name="magic dust",
    version=get_version(),
    author="DevOps Practice",
    author_email="dsahoo@nexient.com",
    description="Provides a cloud and deployment orchestration tool suite.",
    license="Apache License 2.0",
    keywords="jinja2",
    url="https://github.com/nexient-llc/magicdust",
    packages=find_packages(),
    py_modules=['helpers'],
    install_requires=install_requires(),
    long_description='Provides a cloud and deployment orchestration tool suite.',
    classifiers=[
        "Topic :: Utilities",
        "License :: Nexient :: Apache Software License",
        "License :: OSI Approved :: Apache Software License",
    ],
    entry_points={
        "console_scripts": ["magicdust=helpers:main"]
    }
)
