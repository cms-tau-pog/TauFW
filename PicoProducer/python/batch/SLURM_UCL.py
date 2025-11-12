# Author: Izaak Neutelings (Februari 2024)
from TauFW.PicoProducer.batch.SLURM import SLURM

class SLURM_UCL(SLURM):
  """Subclass to load different .sh script."""
  def __init__(self,verb=False):
    super(SLURM_UCL,self).__init__(verb=verb)
  