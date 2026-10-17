"""Runner cache bound; cache is external to committed outputs."""
import json,sys
from fetch_pool import prune
if __name__=='__main__':print(json.dumps(prune(sys.argv[1],int(sys.argv[2])*1024*1024),sort_keys=True))
