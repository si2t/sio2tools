import dataclasses

from bs4 import BeautifulSoup

from user import User
from colorama import Style as S, Fore as F
import colorama
from progressbar import ProgressBar, TICK, XMARK
import bs4
import time
from datetime import datetime
import os
from urllib.parse import urljoin, urlencode
import yaml
from dataclasses import dataclass
import threading

SR = S.RESET_ALL
colorama.init(autoreset=True)

@dataclass
class TestCase:
    id: str
    kind: str
    in_file: str
    out_file: str
    in_file_href: str
    out_file_href: str

@dataclass
class TestGroup:
    prefix: str
    test_cases: list[TestCase]
    time_limit: int
    memory_limit: int
    points: int

class HrefDownloadThiefThread(threading.Thread):
    def __init__(self, name: str, user: User, tasks: list, path: str, pb: ProgressBar, folder_prefix: str):
        super().__init__(name=name)
        self.user = user
        self.tasks = tasks
        self.path = path
        self.pb = pb
        self.name = name
        self.folder_prefix = folder_prefix

    def run(self):
        for i, (filename, href) in enumerate(self.tasks):
            data = self.user.fetch_sio2(href).content
            with open(os.path.join(self.path, self.folder_prefix, filename), "wb") as f:
                f.write(data)
            self.pb.update_next(f"{TICK} [{self.name}] Downloaded {filename} from {href}")

class Module:
    name = "Szkopul Thief"
    description = "Steal packs from Szkopul by copying them to your contest and downloading IN, OUT and other files"


    def __init__(self, data: dict, user: User, sio2url: str):
        self.data = data
        self.user = user
        self.sio2url = sio2url
        self.abort = False

    def fetch_task(self):
        fetch_url = urljoin(self.sio2url, "/problemset/?" + urlencode({"q": self.task_name}))
        print(f"Search URL: {F.BLUE}{fetch_url}, fetching...")
        task_html = self.user.fetch_sio2(fetch_url).text
        print(f"{F.YELLOW} Warning: This will fetch the first result only, if multiple tasks match the search query, you can end up exporting the wrong task{SR}")
        soup = bs4.BeautifulSoup(task_html, "html.parser")
        table = soup.find("table", {"class": "table button-flat"}, recursive=True).find("tbody").find("tr") # first result
        if not table:
            print(f"  {XMARK} Failed to get task, aborting...")
            self.abort = True
            return
        tds = table.find_all("td", recursive=True)
        task_id = tds[0].text.strip()
        task_name = tds[1].text.strip()
        task_href = tds[1].find("a")["href"].strip()
        task_real_id = task_href.split("/")[-3]
        print(f"Found Task: {F.BLUE}{task_name} ({task_id})")
        print(f"UID: {F.BLUE}{task_real_id}")
        submitters = tds[3].text.strip()
        perc_correct = tds[4].text.strip()
        average = tds[5].text.strip()
        try:
            your_score = tds[6].text.strip()
        except:
            your_score = "N/A"
        print(f"  Stats data: {S.DIM}Submitters: {SR}{F.BLUE}{submitters}{SR}, {S.DIM}Correct: {SR}{F.GREEN}{perc_correct}{SR}, {S.DIM}Average: {SR}{F.MAGENTA}{average}{SR}, {S.DIM}Your score: {SR}{F.CYAN}{your_score}")
        print(f"  URL: {F.BLUE}{urljoin(self.sio2url, task_href)}")
        print(f"  Getting CSRF Token...")
        csrftoken = soup.find("form", {"id": "add_to_contest"}).find("input")["value"]

        print("Creating base folder...")
        self.folder = os.path.join(os.path.abspath(self.destination_folder), f"{task_id}-{task_name}-{task_real_id}")
        os.makedirs(self.folder, exist_ok=True)
        print(f"  {S.DIM}Created folder {SR}{F.BLUE}{self.folder}{SR}")

        print("Creating IN files folder...")
        self.in_folder = os.path.join(self.folder, "in")
        os.makedirs(self.in_folder, exist_ok=True)
        print(f"  {S.DIM}Created folder {SR}{F.BLUE}{self.in_folder}{SR}")

        print("Creating OUT files folder...")
        self.out_folder = os.path.join(self.folder, "out")
        os.makedirs(self.out_folder, exist_ok=True)
        print(f"  {S.DIM}Created folder {SR}{F.BLUE}{self.out_folder}{SR}")

        print("Creating PROG folder...")
        self.prog_folder = os.path.join(self.folder, "prog")
        os.makedirs(self.prog_folder, exist_ok=True)
        print(f"  {S.DIM}Created folder {SR}{F.BLUE}{self.prog_folder}{SR}")

        self.csrftoken = csrftoken
        self.task_id = task_real_id
        self.short_id = task_id
        self.task_name = task_name

    def copy_task_to_contest(self):
        if not self.no_copy:
            copy_url = urljoin(self.sio2url, f"/c/{self.contest_id}/problems/add?key=problemset_source")
            print(f"  Copy URL: {F.BLUE}{copy_url}, executing...")
            copy_req = self.user.fetch_sio2(copy_url, method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}, data={"url_key": self.task_id, "csrfmiddlewaretoken": self.csrftoken})
            print(f"Copy status code (302 is OK): {F.BLUE}{copy_req.status_code}")
            if copy_req.status_code == 302:
                print(f"  {TICK} Problem added to the contest properly")
            else:
                print(f"  {XMARK} Could not add problem, maybe it already exists? Fetching...")

        print(f"  Finishing: getting problemset link")
        problems = self.user.fetch_sio2(f"/c/{self.contest_id}/admin/contests/probleminstance/")
        soup = BeautifulSoup(problems.text, "html.parser")
        table = soup.find("table", {"class": "table table-striped"}).find("tbody").find_all("tr")
        found = False
        for t in table:
            if t.find("th").text.strip() == self.task_name:
                print("  Found Task in your contest page")
                edit_href = t.find_all("td")[3].find("a")["href"]
                print(f"  Edit link: {edit_href}")
                self.edit_href = edit_href
                found = True
                break

        if not found:
            print("  No problem found, aborting...")
            self.abort = True
            return

    def fetch_basic_task_data(self):
        print("Downloading task PDF...")
        # https://szkopul.edu.pl/c/{contest_id}/problemset/problem/{id}/statement/
        pdflink = urljoin(self.sio2url, f"/c/{self.contest_id}/problemset/problem/{self.task_id}/statement")
        print(f"  PDF link: {F.BLUE}{pdflink}")
        pdf_req = self.user.fetch_sio2(pdflink).content
        print("Writing PDF...")
        with open(os.path.join(self.folder, "prog", f"{self.short_id}.pdf"), "wb") as f:
            f.write(pdf_req)
        print("Wrote PDF successfully")

        print("Generating base config...")
        config = {
            "title": self.task_name,
            "sinol_task_id": self.short_id,
            "sinol_contest_type": "default",
            "memory_limit": 0, # to be filled, kB
            "time_limit": 0, # to be filled, ms
            "scores": {} # to be filled, e.g. "1": 10, "2": 20, ....
        }
        change_html = self.user.fetch_sio2(self.edit_href).text # containing time, memory and IN/OUT files, grouped
        soup = BeautifulSoup(change_html, "html.parser")
        tests_table = soup.find("div", {"id": "tests"}).find("div", {"class": "card-body"}).find("table").find("tbody").find_all("tr")

        self.ins = []
        self.outs = []
        cls_test_groups = {}
        for test in tests_table:
            tds = test.find_all("td")
            test_id = tds[0].text.strip()
            # strip all non-number characters from test_id
            test_group = "".join(filter(lambda x: x.isdigit(), test_id))
            if not cls_test_groups.get(int(test_group)):
                tl = int(tds[1].find("input")["value"])
                ml = int(tds[2].find("input")["value"])
                pts = int(tds[3].find("input")["value"])
                cls_test_groups[int(test_group)] = TestGroup(test_group, [], tl, ml, pts)
            # append test
            test_case = TestCase(test_id, tds[4].text.strip(), tds[5].text.strip(), tds[6].text.strip(), tds[5].find("a")["href"], tds[6].find("a")["href"])
            cls_test_groups[int(test_group)].test_cases.append(test_case)
            self.ins.append([test_case.in_file, test_case.in_file_href])
            self.outs.append([test_case.out_file, test_case.out_file_href])


        print(f"  {TICK} Fetched test groups")
        for gr in cls_test_groups.values():
            print(f"    {S.DIM}TestGroup_{SR}{gr.prefix}: TL {F.BLUE}{gr.time_limit}{SR}ms, ML {F.MAGENTA}{gr.memory_limit}{SR}kB, {F.GREEN}{gr.points}p{SR}")
            for t in gr.test_cases:
                print(f"      {S.DIM}TestCase_{SR}{t.id}: {F.BLUE}{t.kind}{SR}, IN: {F.MAGENTA}{t.in_file}{SR}, OUT: {F.GREEN}{t.out_file}{SR}")

            if gr.prefix != "0": config["scores"][int(gr.prefix)] = gr.points # 0 is uncounted
            config["time_limit"] = max(config["time_limit"], gr.time_limit)
            config["memory_limit"] = max(config["memory_limit"], gr.memory_limit)

        print("  Writing config.yaml...")
        configpath = os.path.join(self.folder, "config.yaml")
        with open(configpath, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"  {TICK} Wrote config.yaml successfully ({configpath})")


    def fetch_in_files(self):
        print(f"Splitting IN files for {F.BLUE}{self.num_threads}{SR} threads...")
        tasks_for_threads = [[] for _ in range(self.num_threads)]
        counter = 0
        for i, (in_file, in_file_href) in enumerate(self.ins):
            tasks_for_threads[counter % self.num_threads].append([in_file, in_file_href])
            counter += 1

        print("Starting download...")
        with ProgressBar(len(self.ins), color="BLUE", length=80, additional_text="Downloading IN files...") as pb:
            threads = []
            for i in range(len(tasks_for_threads)):
                thread = HrefDownloadThiefThread(f"Thread-{i+1}", self.user, tasks_for_threads[i], self.folder, pb, "in")
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
                pb.update(pb.current_progress, f"{TICK} Thread {thread.name} finished")


    def fetch_out_files(self):
        print(f"Splitting OUT files for {F.BLUE}{self.num_threads}{SR} threads...")
        tasks_for_threads = [[] for _ in range(self.num_threads)]
        counter = 0
        for i, (out_file, out_file_href) in enumerate(self.outs):
            tasks_for_threads[counter % self.num_threads].append([out_file, out_file_href])
            counter += 1

        print("Starting download...")
        with ProgressBar(len(self.ins), color="CYAN", length=80, additional_text="Downloading OUT files...") as pb:
            threads = []
            for i in range(len(tasks_for_threads)):
                thread = HrefDownloadThiefThread(f"Thread-{i + 1}", self.user, tasks_for_threads[i], self.folder, pb,"out")
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()
                pb.update(pb.current_progress, f"{TICK} Thread {thread.name} finished")

    def fetch_model_solution_code(self):
        print("Starting model solution code download...")

    def finalize(self):
        print("Packing to ZIP archive...")

    def execute(self):
        print("SzkopulThief - Steal packs from Szkopul")
        contest_id = self.data.get("contest_id", "")
        destination_folder = os.path.abspath(self.data.get("folder", "."))
        task_name = self.data.get("task_name", "")
        self.contest_id = contest_id
        self.destination_folder = destination_folder
        self.task_name = task_name
        self.no_copy = self.data.get("no_copy", "False").lower() in ["true", "yes", "1"]
        self.num_threads = int(self.data.get("threads", 1))
        print(f"{S.DIM}Contest add ID: {SR}{F.BLUE}{contest_id}")
        print(f"{S.DIM}Pack export folder: {SR}{F.BLUE}{destination_folder}")
        print(f"{S.DIM}Task name: {SR}{F.BLUE}{task_name}")
        print(f"{S.DIM}No copy task to contest: {SR}{F.BLUE}{self.no_copy}")
        print(f"{S.DIM}Number of threads: {SR}{F.BLUE}{self.num_threads}")

        steps = {
            f"Fetching Task {task_name}": self.fetch_task,
            f"Copying to contest {contest_id}": self.copy_task_to_contest,
            f"Fetching basic task data": self.fetch_basic_task_data,
            f"Fetching IN files": self.fetch_in_files,
            f"Fetching OUT files": self.fetch_out_files,
            f"Fetching model solution code": self.fetch_model_solution_code,
            f"Finalizing": self.finalize
        }

        print(f"Will execute {F.BLUE}{len(steps)}{SR} steps")


        all_start = time.time()
        for (i, (step_name, func)) in enumerate(steps.items(), start=1):
            print(f"[{F.BLUE}{i}/{F.GREEN}{len(steps)}{SR}] {step_name}...")
            start = time.time()
            func()
            elapsed = time.time() - start
            if self.abort:
                print("Exiting task loop")
                exit(1)
            print(f"  {F.GREEN}{TICK}{SR} Step {i} complete, took {F.BLUE}{elapsed:.2f}s")

        print(f"All steps complete, took {F.GREEN}{time.time()-all_start:.2f}s")
