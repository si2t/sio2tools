import getpass

from user import User, Auth
from colorama import Fore, Style

class Module:
    name = "Login"
    description = "Safely store your SIO2 credentials for future use. You won't have to provide username/password/sessionid/csrftoken every time you use sio2tools after using this module"
    can_ignore_user = True

    def __init__(self, data: dict, user: User, sio2url: str):
        self.user = user
        self.data = data
        self.sio2url = sio2url

    def execute(self):
        if self.data.get("action") == "remove":
            try:
                self.user.remove_credentials()
                print("Credentials removed successfully.")
                exit(0)
            except:
                print("Failed to remove credentials.")
                exit(1)

        R = Style.RESET_ALL
        if self.user is None:
            print(f"Logging in to SIO2, URL: {self.sio2url}")
            print("Choose method: login [l] or cookie data [c]")
            method = input(f"Method: {Fore.MAGENTA}")
            if method.lower() == "l":
                username = input(R + f"Username: {Fore.MAGENTA}")
                password = getpass.getpass(R + "Password: ")
                if username == "" or password == "":
                    print(R + "Username and password cannot be empty.")
                    exit(1)
                # obtain cookie data
                self.user = User(
                    auth=Auth(username=username, password=password),
                    base_url=self.sio2url,
                )
                self.user.obtain_session_credentials()
            elif method.lower() == "c":
                csrftoken = input(R + f"CSRF Token: {Fore.MAGENTA}")
                sessionid = input(R + f"Session ID: {Fore.MAGENTA}")
                if csrftoken == "" or sessionid == "":
                    print(R + "CSRF Token and Session ID cannot be empty.")
                    exit(1)
                self.user = User(
                    auth=Auth(csrftoken=csrftoken, sessionid=sessionid),
                    base_url=self.sio2url,
                )
            else:
                print(R + "Incorrect login method")
                exit(1)

        self.user.store_credentials(self.sio2url)
        print(R + "Credentials stored successfully in ~/.sio2tools_credentials")
        print("  You can now use sio2tools without providing your credentials.")
        print('  To remove stored credentials, run `python3 sio2tools -m login -d "action=remove"`')
        print("  To see available modules, run sio2tools with the -l flag.")
        print("  To use a module, run sio2tools with the -m flag.")
        print("  For more information, run sio2tools with the -h flag.")
        print("Thank you for using sio2tools!")
        exit(0)
