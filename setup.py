from setuptools import find_packages, setup

setup(
    name="faust2hpp",
    version="0.1",
    packages=["faust2hpp"],
    package_data={
        "faust2hpp": ["Source/*.h"],
    },
    scripts=["scripts/faust2hpp"],
)
