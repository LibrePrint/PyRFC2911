from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


class PPD(object):
    def text(self):
        raise NotImplementedError()

# fuck that cursed shit

class ModelPPD:
    def __init__(self,path):
        with open(path) as file:
            self._content = file.read()
    def text(self):
        return self._content