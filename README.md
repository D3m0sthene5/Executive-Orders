# Pergamon store root

Every `pergamon-xx` release tag of the Pergamon byte store (jobs/_lib/pergamon_store.py) points at this commit. It has
no workflow files, so creating a tag here starts no GitHub Actions run (GitHub ignores path filters on tag pushes, so
tags on ordinary commits started every push workflow). The bytes live in the release assets; manifests live in git.
