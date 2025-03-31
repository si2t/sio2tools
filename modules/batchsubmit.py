from user import User
from utils import submit_solution
from progressbar import ProgressBar, TICK
import time
import requests
import sio2submit
from bs4 import BeautifulSoup
import math
from colorama import Fore, Style

class Module:
    name = "Batch Submit Solution"
    description = "Submit a solution to multiple tasks multiple times"
    can_ignore_user = True
    
    def __init__(self, data: dict, user: User | None, sio2url: str):
        self.user = user
        self.data = data
        self.sio2url = sio2url
        
    def execute(self):
        tasks = self.data.get("tasks", "").split(",")
        contest = self.data.get("contest", "28orly")
        num_submits = self.data.get("num_submits", 0)
        codefile = self.data.get("codefile", "")
        tasksfile = self.data.get("tasksfile", "")
        threads = int(self.data.get("threads", 1))
        wait = float(self.data.get("wait", 1))
        token = self.data.get("token", "")
        if tasks == [""]:
            tasks = []
        
        if not token and not self.user:
            raise ValueError("No token provided and no user logged in")
        
        url = requests.compat.urljoin("https://wyzwania.programuj.edu.pl/c/", contest)
        if not token:
            # we have to obtain the SIO2 submit token
            sio2obtain_token_endpoint = f"c/{contest}/submitservice/view_user_token/"
            token_page = self.user.fetch_sio2(sio2obtain_token_endpoint).text
            soup = BeautifulSoup(token_page, "html.parser")
            
            # python submit.py -u https://wyzwania.programuj.edu.pl/c/28orly/ -k <token> -s
            kbd_execute_token = soup.find("kbd").text.strip()
            # get the token from text
            token = kbd_execute_token.split(" ")[-2]
        
        # configure sio2submit before submitting
        print("Successfully obtained submit token")
        
        sio2submit.configuration = {
            "token": token,
            "contest-url": url
        }
        print("Got data:")
        if tasks: print(" * Tasks:", tasks)
        print(" * Contest:", contest)
        if num_submits: print(" * Number of submits:", num_submits)
        if codefile: print(" * Code file:", codefile)
        if tasksfile: print(" * Tasks file (optional, ignores tasks list):", tasksfile)
        print(" * Number of threads:", threads)
        print(" * Wait time between submits:", wait, "s =", math.floor(wait/3600), "hours,", math.floor((wait-math.floor(wait/3600)*3600)/60), "minutes,", math.floor(wait%60), "seconds")
        
        task_mapping = {}
        total_tasks = 0
        
        if tasksfile:
            with open(tasksfile, "r") as file:
                temptasks = file.read().splitlines()
                for t in temptasks:
                    name, num, code = t.split(":")
                    task_mapping[name] = [int(num), code]
                    total_tasks += int(num)
        else:
            for t in tasks:
                task_mapping[t] = [num_submits, codefile]
            total_tasks = len(tasks) * num_submits
        
        print(f"\n{Fore.MAGENTA}Will submit {Style.BRIGHT}{total_tasks}{Style.NORMAL} tasks in total")
        for task, (num, code) in task_mapping.items():
            print(f" * {task}: {num} times, code file: {code}")
            
        estimated_time = total_tasks * (wait + 1)
        estimated_min, estimated_s = divmod(estimated_time, 60)
        estimated_h, estimated_min = divmod(estimated_min, 60)
        estimated_h, estimated_min, estimated_s = int(estimated_h), int(estimated_min), int(estimated_s)
        print(f"\nEstimated time to complete: {Fore.BLUE}{estimated_h}h {estimated_min}m {estimated_s}s{Style.RESET_ALL}")
            
        i = 0
        with ProgressBar(max_value=total_tasks, color="RED", length=80, additional_text="Submitting tasks") as pb:
            for task, (num, code) in task_mapping.items():
                for i in range(num):
                    submit_solution(token, url, task, code, False)
                    pb.update_next(f"{TICK} [{i+1}/{num}] Submitted task {task} with code file {code}")
                    i += 1
                    if i < total_tasks: time.sleep(wait)
            