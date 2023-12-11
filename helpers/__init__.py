print("--- Import helpers ---")

import os
os.environ['USE_PYGEOS'] = '0'

from . import scrapping
from . import visualize
from . import basicstatistics

#to assure that reload(helpers) reloads everything in the folder.
from importlib import reload
reload(scrapping)
reload(visualize)
reload(basicstatistics)

#to not have to import each file separetly.
from .scrapping import *
from .visualize import *
from .basicstatistics import *
