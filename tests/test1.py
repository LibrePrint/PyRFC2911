# NOTE: 
# Set "ppd" environment variable to a ppd as a string.
# e.g. ppd=$(cat ~/some_printer.ppd) python test1.py

######################################################
#                    Fix path                        #
from os import environ                               #
import sys;sys.path.append(".");sys.path.append("..")#
######################################################

from rfc2911.adapter import BaseAdapterClass
from rfc2911.behaviour import ModelBehaviour
from rfc2911.server import IPPServer

with open("tests/test.ppd") as file:
    server = IPPServer(
        "127.0.0.1",
        8000,
        "127.0.0.1:8080",
        ModelBehaviour(
            adapter=BaseAdapterClass(file.read())
        ),
    )
    server.run()