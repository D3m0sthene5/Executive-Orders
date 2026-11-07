"""Run a Python script with pathlib rendering paths with forward slashes (the containers ran on Linux)."""
import pathlib, runpy, sys, os
_orig = pathlib.PurePath.__str__
_BS = chr(92)
def _s(self): return _orig(self).replace(_BS, '/')
pathlib.PurePath.__str__ = _s
script = os.path.abspath(sys.argv[1]); sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(script))
runpy.run_path(script, run_name='__main__')
