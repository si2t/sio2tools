import argparse
import utils
from user import User, Auth

parser = argparse.ArgumentParser(description="SIO2 Tools", epilog="by @konradsic")
parser.add_argument("-u", "--username", help="Username for SIO2", type=str)
parser.add_argument("-p", "--password", help="Password for SIO2", type=str)
parser.add_argument("-s", "--sessionid", help="Session ID for SIO2", type=str)
parser.add_argument("-t", "--csrftoken", help="CSRF Token for SIO2", type=str)
parser.add_argument("-m", "--module", help="Module to use", type=str)
parser.add_argument("-d", "--data", help="Data to pass to extension", type=str)
parser.add_argument(
    "-l", "--list-extensions", help="List available extensions", action="store_true"
)
parser.add_argument("--sio2url", help="SIO2 Base URL", type=str, default="https://wyzwania.programuj.edu.pl/")

args = parser.parse_args()

if args.list_extensions:
    utils.list_extensions()
    exit(0)

sio2url = args.sio2url
user = None
if not utils.can_module_ignore_user(args.module):    
    if not ((args.username and args.password) or (args.sessionid and args.csrftoken)):
        user = User.load_credentials_from_file(sio2url)
    else:
        user = User(Auth(args.username, args.password, args.csrftoken, args.sessionid), base_url=sio2url)
else:
    print("[INFO] This module does not require user credentials")

utils.execute_module(args.module, args.data or "", user, sio2url)
