from fastapi import FastAPI
import os
import requests
from bs4 import BeautifulSoup
from classes import RankingUser, Ranking
import time
import json
import datetime

app = FastAPI()

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

    
@app.get("/test_item/{item_id}")
def read_item(item_id: str):
    return {"itemid": item_id, "hello": "world"}

@app.get("/sio2/ranking/changes/all")
def sio2ranking_allchanges():
    pass

@app.get("/sio2/ranking/changes/new")
def new_sio2ranking_changes():
    pass

@app.get("/sio2/ranking/all")
def all_sio2ranking():
    return fetch_sio2_ranking().json()

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
            
        