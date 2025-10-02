# Author: Izaak Neutelings (February 2022)
import os
from TauFW.common.tools.log import Logger, color, bold
from TauFW.PicoProducer.storage.utils import LOG as SLOG
import TauFW.PicoProducer.tools.config as GLOB
os.chdir(GLOB.basedir)
CONFIG = GLOB.getconfig(verb=0) # load once
LOG    = Logger()