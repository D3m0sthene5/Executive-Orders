import sys
sys.path.insert(0,'/home/user/Executive-Orders/jobs/_lib')
import eo_identity as e
d=e.load_dates('/home/user/Executive-Orders')
for k in ('EO:8969','EO:10276','EO:8967','EO:10271'): print(k,d.get(k))
