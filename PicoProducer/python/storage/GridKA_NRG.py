#! /usr/bin/env python
# Author: Sebastian Brommer (July 2020)
from past.builtins import basestring # for python2 compatibility
import os
from TauFW.common.tools.utils import execute
from TauFW.PicoProducer.storage.StorageSystem import StorageSystem
import getpass, platform


class GridKA_NRG(StorageSystem):
    def __init__(self, path, verb=0, ensure=False):
        """NRG Storage at GridKA"""
        super(GridKA_NRG, self).__init__(path, verb=verb, ensure=False)
        self.lscmd = "xrdfs"
        self.lsurl = "root://cmsxrootd-kit.gridka.de/ ls "
        self.rmcmd = "xrdfs"
        self.rmurl = "root://cmsxrootd-kit.gridka.de/ ls "
        self.mkdrcmd = "xrdfs"
        self.mkdrurl = 'root://cmsxrootd-kit.gridka.de/ mkdir -p '
        self.cpcmd = 'xrdcp -f'
        self.cpurl = "root://cmsxrootd-kit.gridka.de/"
        self.tmpdir = '/tmp/'
        self.fileurl = "root://cmsxrootd-kit.gridka.de/"
        self.localmount = "/storage/gridka-nrg/"
        if ensure:
            self.ensuredir(self.path)

    def ensure_local_temp_dir(self, tmpdir, verb):
        """Ensure local tempdir exists."""
        if verb >= 2:
            print(">>> Creating temp directory {} if not existent yet".format(tmpdir))
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
        return True

    def remove_local_temp_dir(self, tmpdir, verb):
        """Remove local tempdir."""
        if verb >= 2:
            print(">>> removing temp directory {}/* ".format(tmpdir))
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        return True

    def hadd(self, sources, target, **kwargs):
        """
    Hadd files. For NRG we use the local mountpoint at 
    /storage/gridka-nrg for this, merge locally 
    and then move the file back to NRG.
    os.path.relpath(old_path, '/abc/dfg/')
    """
        target = self.expandpath(target, here=True)
        verb = kwargs.get('verb', self.verbosity)
        tmpdir = kwargs.get('tmpdir', target.startswith(self.parent))
        htarget = target
        if tmpdir:
            tmpdir = os.path.join(self.tmpdir, os.environ['USER'])
            self.ensure_local_temp_dir(tmpdir, verb=verb)
            htarget = os.path.join(tmpdir, os.path.basename(target))
        if isinstance(sources, basestring):
          sources = [sources]
        source = ""
        for i, file in enumerate(sources, 1):
            source += os.path.join(self.localmount,
                                   os.path.relpath(file, '/store/user/'))
        source = source.strip()
        if verb >= 2:
            print(">>> %-10s = %r" % ('sources', sources))
            print(">>> %-10s = %r" % ('source', source))
            print(">>> %-10s = %r" % ('target', target))
            print(">>> %-10s = %r" % ('htarget', htarget))
        out = self.execute("%s %s %s" % (self.haddcmd, htarget, source),
                           verb=verb)
        if tmpdir:
            cpout = self.cp(htarget, target, verb=verb)
            self.remove_local_temp_dir(os.path.dirname(htarget), verb=verb)
        return out
