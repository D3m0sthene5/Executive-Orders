#!/usr/bin/env python3
"""Invoke unmodified PR59 kit modules against explicit shared repository inputs."""
import pathlib,sys
repo=pathlib.Path(__file__).resolve().parents[5]
snapshot=repo.parent/'continuous-prechange'
sys.path[:0]=[str(snapshot),str(repo/'jobs/claim-kit')]
import kit
raise SystemExit(kit.main(['--repo',str(repo),'--output',str(repo/'tmp/continuous-compiled')]+sys.argv[1:]))
