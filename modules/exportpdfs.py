from user import User
from bs4 import BeautifulSoup
from utils import get_contest_names, datatable
import time
import os
from progressbar import ProgressBar, TICK
from threading import Thread

class PDFExportingThread(Thread):
    def __init__(
        self,
        name: str,
        user: User,
        tasks: list,
        path: str,
        pb: ProgressBar,
        categorize: bool
    ):
        super().__init__()
        self.user = user
        self.tasks = tasks
        self.path = path
        self.pb = pb
        self.categorize = categorize
        
    def run(self):
        for t in self.tasks:
            if self.categorize:
                contest_id, task_name, task_link, round_id = t
            else:
                contest_id, task_name, task_link = t
            pdf_html = self.user.fetch_sio2(task_link).content
            
            if not self.categorize:
                pdf_path = os.path.join(self.path, contest_id, f"{task_name}.pdf")
            else:
                pdf_path = os.path.join(self.path, contest_id, round_id, f"{task_name}.pdf")
            
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(pdf_html)
            
            self.pb.update_next(f"{TICK} [{self.name}] Downloaded {task_name} from contest {contest_id} to {pdf_path}")

class Module:
    name = "Export Task PDFs"
    description = "Export task PDF files from your sio2 contests"

    def __init__(self, data: dict, user: User, sio2url: str):
        self.data = data
        self.user = user
        self.sio2url = sio2url

    def execute(self):
        global_start = time.time()
        destination = self.data.get("path", "pdfs")
        contests = self.data.get("contest", "").split(",")
        categorize = bool(self.data.get("categorize", False))
        num_threads = int(self.data.get("threads", 1))
        if contests == [""]:
            contests = []
        
        print("Got data:")
        print(" * Export folder path:", destination)
        print(" * Contest:", ", ".join(contests) or "All contests")
        print(" * Threads:", num_threads)
        print(" * Categorize:", categorize)
        
        
        # get all contests that match
        contests_tab = []
        print("\nFetching contests...")
        
        # get contest list
        fetched_contests = get_contest_names(self.user)
        
        for c in fetched_contests:
            if c[0] in contests or contests == []:
                contests_tab.append(c)
                
        print("Found", len(contests_tab), "contests")
        datatable(contests_tab, ["ID", "Name"])
        
        # Create folders
        print("\nCreating folders...")
        if not os.path.exists(destination):
            os.makedirs(destination, exist_ok=True)
        
        # create subfolders for problems
        for contest in contests_tab:
            contest_id = contest[0]
            contest_folder = os.path.join(destination, contest_id)
            os.makedirs(contest_folder, exist_ok=True)
            print(" * Created folder for contest", contest[1], "at", contest_folder)
        
        print("\nPreparing tasks for download...")
        # pre-fetch task names for total number of tasks
        tasks = []
        total_tasks = 0
        contests_len = len(contests_tab)
        
        for i, contest in enumerate(contests_tab):
            start = time.time()
            contest_id = contest[0]
            contest_name = contest[1]
            print(f" * [{i+1}/{contests_len}] Fetching tasks from contest", contest_name, "...", end=" ")
            
            tasks_html = self.user.fetch_sio2(f"c/{contest_id}/p/").text
            tasks_soup = BeautifulSoup(tasks_html, "html.parser")
            table = tasks_soup.find("table", {"class": "table table-striped table--narrow"}).find("tbody")
            tasks_containers = table.find_all("tr")
            cur_tasks = 0
            
            for task in tasks_containers:
                if "problemlist-subheader" in task.get("class", []):
                    if not categorize: continue
                    round_id = task.find("td").find("strong").text.strip()
                    round_folder = os.path.join(destination, contest_id, round_id)
                    os.makedirs(round_folder, exist_ok=True)
                    print(" * Created folder for round", round_id, "contest", contest_name, "at", round_folder)
                    continue
                
                task_id, task_name, *_ = task.find_all("td")
                task_id = task_id.text.strip()
                task_href = task_name.find("a").get("href")
                task_name = task_name.find("a").text.strip()
                fmt_task_name = f"{task_name} ({task_id})"
                
                if not categorize: 
                    tasks.append((contest_id, fmt_task_name, task_href))
                else:
                    tasks.append((contest_id, fmt_task_name, task_href, round_id))
                cur_tasks += 1
                
            total_tasks += cur_tasks
            print(f"done, found {cur_tasks} problems in {time.time()-start:.2f}s")
            
        print("\nFound", total_tasks, "tasks, downloading PDFs...")
        
        tasks_for_therads = [[] for _ in range(num_threads)]
        counter = 0
        for task in tasks:
            tasks_for_therads[counter % num_threads].append(task)
            counter += 1

        for i in range(len(tasks_for_therads)):
            print(
                f"  Thread-{i+1} will download {len(tasks_for_therads[i])} task PDFs"
            )
            
        threads = [] # for holding threads
        
        with ProgressBar(total_tasks, color="BLUE", length=80, additional_text="Downloading task PDFs...") as pb:
            for i in range(num_threads):
                thread_tasks = tasks_for_therads[i]

                thread = PDFExportingThread(
                    f"Thread-{i+1}",
                    self.user,
                    thread_tasks,
                    destination,
                    pb,
                    categorize
                )
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
            
        mins, secs = divmod(time.time() - global_start, 60)
        mins = round(mins)
        if not mins:
            s = f"{secs:.0f}"
        else:
            s = f"{secs:02.0f}"
        
        print(f"Downloaded all tasks in {str(mins) + ' minutes, ' if mins else ''}{s} seconds")
        print(f" View them at {os.path.abspath(destination)}")