from user import User
from utils import submit_solution
import requests
from bs4 import BeautifulSoup
import sio2submit

class Module:
    name = "Submit Solution"
    description = "Submit a solution to a task"
    can_ignore_user = True
    
    def __init__(self, data: dict, user: User | None, sio2url: str):
        self.user = user
        self.data = data
        self.sio2url = sio2url
    
    def execute(self):
        print("data", self.data)
        token = self.data.get("token", "")
        print("token", token)
        if not token and not self.user:
            raise ValueError("No token provided and no user logged in")

        contest = self.data.get("contest", "28orly")
        url = requests.compat.urljoin("https://wyzwania.programuj.edu.pl/c/", contest, "/")
        
        if not token:
            print("Fetching token from user account")
            # we have to obtain the SIO2 submit token
            sio2obtain_token_endpoint = f"c/{contest}/submitservice/view_user_token/"
            token_page = self.user.fetch_sio2(sio2obtain_token_endpoint).text
            soup = BeautifulSoup(token_page, "html.parser")
            
            # python submit.py -u https://wyzwania.programuj.edu.pl/c/28orly/ -k <token> -s
            kbd_execute_token = soup.find("kbd").text.strip()
            # get the token from text
            token = kbd_execute_token.split(" ")[-2]
        
        # configure sio2submit before submitting
        sio2submit.configuration = {
            "token": token,
            "contest-url": url
        }
        print("Successfully obtained submit token")
        
        taskname = self.data.get("task", "")
        file = self.data.get("file", "")
        #contest = self.data.get("contest", "28orly")
        webbrowser = self.data.get("webbrowser", "")
        if webbrowser.lower() in ["True", "yes", "1"]:
            webbrowser = True
        else:
            webbrowser = False
        
        print("Got data:")
        print(" * Task:", taskname)
        print(" * Submit code file:", file)
        print(" * Open webbrowser:", webbrowser)
        
        print("Submitting...")
        submit_solution(token, url, taskname, file, webbrowser)
        
