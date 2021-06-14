from setuptools import setup, find_packages

setup(
    name='mtwlib',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'paramiko>=2.7.1'
    ]
)
