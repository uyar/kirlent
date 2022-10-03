__version__ = "0.1.2"

from invoke import Collection, Program

from . import tasks


program = Program(namespace=Collection.from_module(tasks), version=__version__)
