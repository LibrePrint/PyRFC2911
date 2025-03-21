"""
Python library for creating printers.
Usage:
    
>>> from .behaviour import ModelBehaviour
>>> from .server import IPPServer
>>> from .adapter import BaseAdapterClass
>>> 
>>> class MyAdapter(BaseAdapterClass): ... # See documentation
>>> IPPServer(
>>>     "0.0.0.0",
>>>     631,
>>>     "http://127.0.0.1:3000/controlpanel",
>>>     ModelBehaviour(
>>>         True,
>>>         ".",
>>>         ppd_path="~/model.ppd",
>>>     )
>>> )

See documentation for details.
"""

from .behaviour import ModelBehaviour
from .adapter import BaseAdapterClass,BaseBrandingClass
from .server import IPPServer