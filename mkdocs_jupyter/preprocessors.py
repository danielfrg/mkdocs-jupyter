from copy import deepcopy

from nbconvert.preprocessors import Preprocessor
from traitlets import Integer


class SliceIndex(Integer):
    """An integer trait that accepts None
    Used by the SubCell Preprocessor"""

    default_value = None

    def validate(self, obj, value):
        if value is None:
            return value
        else:
            return super(SliceIndex, self).validate(obj, value)


class SubCell(Preprocessor):
    """A preprocessor to select a slice of the cells of a notebook"""

    start = SliceIndex(0, config=True, help="First cell of notebook")
    end = SliceIndex(None, config=True, help="Last cell of notebook")

    def preprocess(self, nb, resources):
        nbc = deepcopy(nb)
        nbc.cells = nbc.cells[self.start : self.end]
        return nbc, resources
