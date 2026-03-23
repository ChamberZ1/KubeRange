from setuptools import setup, find_packages

setup(
    name="kuberange-common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy",
        "kubernetes",
    ]
)