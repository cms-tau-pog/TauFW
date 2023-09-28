# Author: Izaak Neutelings (June 2023)
from TauFW.PicoProducer.batch.HTCondor import HTCondor

class HTCondor_DESY(HTCondor):
  """Subclass to load different .sub script."""
  def __init__(self,verb=False):
    super(HTCondor_DESY,self).__init__(verb=verb)
  