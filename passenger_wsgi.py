#!/home/podcasts_user/opt/python-3.6.2/bin/python3
import sys, os

INTERP = '/home/{}/podcasts.irumble.com/venv/bin/python3'.format(os.environ['USER'])


#INTERP is present twice so that the new Python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())
from app import app as application
