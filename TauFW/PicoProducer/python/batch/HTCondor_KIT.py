# Author: Izaak Neutelings (June 2023)
from TauFW.PicoProducer.batch.HTCondor import HTCondor

class HTCondor_KIT(HTCondor):
  """Subclass to load different .sub script."""
  def __init__(self,verb=False):
    super(HTCondor_KIT,self).__init__(verb=verb)
  