import json
import os
import requests
from bs4 import BeautifulSoup
import time
import datetime

class Task:
    def __init__(self, name: str, points: int | None):
        self.name: str = name
        self.points: int | None = points
        
    def json(self):
        return {"name": self.name, "points": self.points}

class Ranking:
    def __init__(self, contest_name: str):
        self.contest_name: str = contest_name
        self.tasks: list[str] = []
        self.users: list[RankingUser] = []
        
    def json(self):
        return {
            "contest": self.contest_name,
            "tasks": self.tasks,
            "users": list(u.json() for u in self.users)
        }
        
    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.json(), f, indent=2, ensure_ascii=False)
            
    def compare(self, other):
        res = []
        for (usr1, usr2) in zip(self.users, other.users):
            if usr1.name != usr2.name:
                continue
            for (t1, t2) in zip(usr1.tasks, usr2.tasks):
                if t1.name != t2.name:
                    return []
                if t1.points != t2.points:
                    res.append({
                        "user": usr1.name,
                        "task": t1.name,
                        "old_points": t2.points,
                        "new_points": t1.points
                    })
                    
        return res
        
    
class RankingUser:
    def __init__(self, name: str, idx: int, sum_points: int | None = None, tasks: list[Task] = None):
        if tasks == None:
            tasks = []
        self.idx: int = idx
        self.name: str = name
        self.tasks: list[Task] = tasks
        self.sum_points: int | None = sum_points
        
    def append_task(self, name: str, points: int | None):
        taskcls = Task(name, points)
        self.tasks.append(taskcls)
        
    def json(self):
        return {
            "idx": self.idx,
            "name": self.name,
            "sum_points": self.sum_points,
            "tasks": list(t.json() for t in self.tasks)
        }

JSONSAVE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '28orlynotifs.json')

TEST_CSRFTOKEN = "tydSeEmr5uAnANuQi5AMxZGDDixsuhPN"
TEST_SESSIONID = "ehe23l5al8wcaalwi803tcsf5aa5h4fu"
WEBHOOK_ID = "1321925459419729920"
WEBHOOK_TOKEN = "9DuFGrea2ukUpGnGfZm2XC6xtgXqW6toCHnsJBO1lomx6YVAVC8BWEimQOZ5yn9nW040"

def fetch_sio2_ranking(csrftoken: str, sessionid: str, contest_name: str="28orly"):
    urlpath = f"https://wyzwania.programuj.edu.pl/c/{contest_name}/ranking/"
    headers = {"Cookie": f"csrftoken={csrftoken}; sessionid={sessionid}; lang=en"}
    
    data = requests.get(urlpath, headers=headers)
    soup = BeautifulSoup(data.text, "html.parser")
    
    ranking_table = soup.find(class_="table table-ranking table-striped table-sm submission")
    result_ranking = Ranking(contest_name)
    
    # task names
    task_names = []
    task_container = ranking_table.find("thead").find("tr").find_all("th")[3:]
    
    for single_task in task_container:
        task_names.append(single_task.text.strip())
        
    result_ranking.tasks = task_names
    
    ranking_users = ranking_table.find("tbody").find_all("tr", recursive=False)
    
    for user in ranking_users:
        idx = int(user.find_all("td")[0].text.strip())
        name = user.find(class_="user-cell").text.strip()
        sum_points = int(user.find_all("td")[2].text.strip())
        usr_class = RankingUser(name, idx, sum_points)
        
        for i, task in enumerate(user.find_all("td")[3:]):
            verdict = task.find("span").text.strip()
            # try to int
            try: verdict = int(verdict)
            except: pass
            
            taskname = task_names[i]
            usr_class.append_task(taskname, verdict)
        
        result_ranking.users.append(usr_class)
        
    return result_ranking
    
def send_webhook(message: str):
    print("Sending webhook message... (url:", f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{WEBHOOK_TOKEN})")
    requests.post(f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{WEBHOOK_TOKEN}", headers={"Content-Type": "application/json"}, json={"content": message})

if __name__ == "__main__":
    # get current state
    prev = fetch_sio2_ranking(TEST_CSRFTOKEN, TEST_SESSIONID)
    
    SLEEP = 1
    while True:
        time.sleep(SLEEP)
        dt = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"[{dt}] Re-fetching ranking...")
        now = fetch_sio2_ranking(TEST_CSRFTOKEN, TEST_SESSIONID)
        results = now.compare(prev)
        if results:
            print("   * Recieved new data:")
            print(json.dumps({"data": results}))
            for x in results:
                usr = x["user"]
                t = x["task"]
                old = x["old_points"]
                if old == "" or old == None: old = "brak"
                new = x["new_points"]
                if new == "" or new == None: new = "brak"
                
                send_webhook(f"## Nowe dane w rankingu `28orly`!\n* 🙋‍♂️ **Kto** : {usr}\n* 📜 **Kod zadania** : `{t}`\n* ✏️ **Punkty**: `{old}` ➜ `{new}`\n*{dt}*")
            prev = now
            
            with open(JSONSAVE, "r") as f:
                content = json.load(f)
                
            content[dt] = results
            
            with open(JSONSAVE, "w") as f:
                json.dump(content, f, indent=2)
            
        