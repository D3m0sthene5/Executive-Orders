import os
from pathlib import Path
from build import run
if __name__=='__main__':
    import tiktoken
    enc=tiktoken.get_encoding('cl100k_base')
    run(Path(os.environ['REPO_ROOT']),Path(os.environ['OUTPUT_DIR']),lambda s:enc.encode(s,disallowed_special=()))
