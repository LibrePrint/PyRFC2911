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