from setuptools import setup, find_packages

setup(
    name="hex",
    version="0.1",
    packages=find_packages(include=['backend', 'backend.*']),
    python_requires=">=3.8",
)