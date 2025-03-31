from user import User
from colorama import Fore, Style
from utils import get_contest_names, datatable
from bs4 import BeautifulSoup
from classes import Problem, Round

class Module:
    name = "Submit Browser"
    description = "Browse your sio2 submissions"
    
    def __init__(self, data: dict, user: User, sio2url: str):
        self.user = user
        self.data = data
        self.sio2url = sio2url
        
    def _browse_contest(self, contest_id: str):
        while True:
            print("Select action number")
            print(" 1. Browse submissions")
            print(" 2. Browse problems")
            print(" 4. Exit from this contest")
            
            try:
                op = int(input(f" >>> {Fore.GREEN}"))
            except:
                print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
                continue
            
            if op == 3: 
                print(Fore.RED + "Exited from contest " + contest_id)
                return
            if op == 1:
                problems = []
                rounds = []
                print("Loading problems...", end="\r")
                problems_html = self.user.fetch_sio2(f"c/{contest_id}/p/").text
                soup = BeautifulSoup(problems_html, "html.parser")
                table = soup.find("table", {"class": "table table-striped table--narrow"}).find("tbody")
                tasks_containers = table.find_all("tr")
                current_round = None
                
                for task in tasks_containers:
                    if "problemlist-subheader" in task.get("class", []):
                        ins = task.find("td")
                        round_name = ins.find("strong").text.strip()
                        round_date_range = ins.find("em").text.strip()
                        rounds.append(Round(round_name, round_date_range))
                        continue
                    problem_id, problem_name, tries_left, user_score = task.find_all("td")
                    problem_id = problem_id.text.strip()
                    problem_name = problem_name.text.strip()
                    problem_url = problem_name.find("a").get("href")
                    tries_left = tries_left.text.strip()
                    user_score = user_score.text.strip()
                    best_solution_sub_url = user_score.find("a").get("href")
                    
                    
                    problems.append(Problem(
                        problem_name,
                        problem_id,
                        int(user_score) if user_score else None,
                        problem_url,
                        tries_left,
                        best_solution_sub_url,
                        current_round
                    ))
                    
                    print("Problems loaded: ", len(problems), end="\r")
                    while True:
                        print(f"Browse problems: enter query, {Fore.BLUE}:help{Style.RESET_ALL} for help, {Fore.RED}:q{Style.RESET_ALL} to quit")
                        q = input(f" >>> {Fore.GREEN}")
                        if q == ":q": break
                        if q == ":help":
                            print("Available commands:")
                            print(" 1. <problem ID> - browse problem")
                            print(" 2. : - list all problems")
                            print(" 3. :q - quit")
                            continue
        
        
    def execute(self):
        print("Launching submit browser...")
        while True:
            print(f"Please select a contest: {Fore.MAGENTA}type in the contest name{Style.RESET_ALL} or {Fore.BLUE}:list{Style.RESET_ALL} to list all contests, {Fore.RED}:q{Style.RESET_ALL} to quit")
            op = input(f" >>> {Fore.GREEN}")
            fetched_contests = get_contest_names(self.user)
            if op == ":q": break
            if op == ":list":
                print("Loading contests...", end="\r")
                print("Your contests:     ")
                datatable(list([(i, a, b) for (i, (a, b)) in enumerate(fetched_contests, start=1)]), ["#", "ID", "Name"])
                print(f"Select a contest by typing {Fore.MAGENTA}.<contest #>{Style.RESET_ALL} or {Fore.BLUE}contest ID{Style.RESET_ALL}")
                opx = input(f" >>> {Fore.GREEN}")
                if opx.startswith("."):
                    try:
                        opx = fetched_contests[int(opx[1:])-1][0]
                    except:
                        print(f"{Fore.RED}Invalid contest number{Style.RESET_ALL}")
                op = opx
            
            # check if contest id is real, else continue in the general loop
            if not any(op == x[0] for x in fetched_contests):
                print(f"{Fore.RED}Invalid contest ID{Style.RESET_ALL}")
                continue
            print()
            print(f"Selected contest:{Fore.MAGENTA}", op)
            self._browse_contest(op)