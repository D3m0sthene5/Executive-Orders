#!/usr/bin/env python3
"""Invoke and assert unmodified PR59 modules against explicit repository inputs."""
import pathlib,sys
repo=pathlib.Path(__file__).resolve().parents[5]
snapshot=repo.parent/'continuous-prechange'
sys.path[:0]=[str(snapshot),str(repo/'jobs/claim-kit')]
# The unchanged assembler prepends its directory; import it before restoring order.
import assemble
sys.path[:0]=[str(snapshot),str(repo/'jobs/claim-kit')]
import prior_research,batch,status_overlay,kit
for module in (prior_research,batch,status_overlay,kit):
    assert pathlib.Path(module.__file__).resolve().parent == snapshot.resolve(),module.__file__
raise SystemExit(kit.main(['--repo',str(repo),'--output',str(repo/'tmp/continuous-compiled')]+sys.argv[1:]))
