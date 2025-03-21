######################################################
#                    Fix path                        #
import sys;sys.path.append(".");sys.path.append("..")#
######################################################

from rfc2911.adapter import BaseAdapterClass,BaseBrandingClass
from rfc2911.behaviour import ModelBehaviour
from rfc2911.server import IPPServer
from os import environ

print(BaseBrandingClass.from_ppd(environ["ppd"]).__dict__)

IPPServer(
    "127.0.0.1",
    8000,
    "127.0.0.1:8080",
    ModelBehaviour(
        adapter=BaseAdapterClass(ppd=environ["ppd"])
    ),
).run()