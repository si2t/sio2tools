from user import User
from classes import Submission
from progressbar import ProgressBar
from bs4 import BeautifulSoup
import os
import threading


def get_all_contest_names(user: User):
    try:
        data = user.fetch_sio2("contest/")
        soup = BeautifulSoup(data.text, "html.parser")
        table = soup.find("div", class_="table-responsive-md").find("tbody")
        contests = []

        for row in table.find_all("tr"):
            cid = row.find("td").text.strip()
            contests.append(cid)

        return contests
    except:
        return []


def get_submissions_list(user: User, data: dict):
    contest = data.get("contest", "28orly")
    all_contests = False
    if contest == "all":
        all_contests = True

    def helper(contest: str):
        cur = 1
        print("\nFetching contest", contest)
        submissions = []
        while True:
            try:
                print(f"  Fetching page {cur}, ", end="")
                data = user.fetch_sio2(f"c/{contest}/submissions/?page=" + str(cur))
                print("processing...", end=" ")
                # print(data.text)
                soup = BeautifulSoup(data.text, "html.parser")
                table = soup.find("table", class_="table table-sm submission")
                rows = table.find_all("tr")[1:]
                if len(rows) == 0:
                    break
                for row in rows:
                    tds = row.find_all("td")
                    if len(tds) >= 5:
                        submission = Submission()
                        submission.submission_time = tds[1].text.strip()
                        submission.name = tds[2].text.strip()
                        submission.status = tds[4].text.strip()
                        if tds[5].text.strip() != "":
                            submission.points = int(tds[5].text.strip())
                        submission.url = tds[6].find("a")["href"]
                        submission.contest_id = contest
                        submissions.append(submission)
            except:
                print("  [!] Error occurred, exiting search loop")
                break

            cur += 1
            print("done")
        return submissions

    ret_submissions = []
    if all_contests:
        contests = get_all_contest_names(user)
        print(
            "Found contests:\n",
            "\n".join(f"  {i}. {name}" for i, name in enumerate(contests, 1)),
        )
        for c in contests:
            ret_submissions.extend(helper(c))
    else:
        ret_submissions = helper(contest)

    return (contest if contest != "all" else contests), ret_submissions


def fetch_code_for_single(user: User, submission: Submission):
    url = submission.url + "source/"
    data = user.fetch_sio2(url)
    soup = BeautifulSoup(data.text, "html.parser")
    code = soup.find("td", class_="code").text
    return code


class CodeFetchingThread(threading.Thread):
    def __init__(
        self,
        name: str,
        user: User,
        submissions: list[Submission],
        progress: ProgressBar,
        folder: str,
    ):
        super().__init__()
        self.user = user
        self.submissions = submissions
        self.progress = progress
        self.name = name
        self.folder = folder

    def run(self):
        for sub in self.submissions:
            code = fetch_code_for_single(self.user, sub)
            short_name = sub.name.split("(")[1].strip("").strip(")")

            with open(
                f"./{self.folder}/{sub.contest_id}/{short_name}_{sub.id}.cpp", "w"
            ) as f:
                f.write("// " + str(sub) + "\n" + code)
            self.progress.update_next(
                with_message=f"[{self.name}] Fetched {short_name} -- {sub.id} ({sub.points} p)"
            )


def fetch_code_all(
    data: dict, user: User, submissions: list[Submission], contests: list[str]
):
    total = len(submissions)
    os.makedirs("./" + data["exportfolder"], exist_ok=True)
    for i, c in enumerate(contests):
        print(
            f"  {i+1}/{len(contests)}. Making directory",
            "./" + data["exportfolder"] + "/" + c,
        )
        os.makedirs("./" + data["exportfolder"] + "/" + c, exist_ok=True)

    num_threads = int(data.get("threads", 1))
    # Calculate the number of submissions per thread
    submissions_for_threads = [[] for _ in range(num_threads)]
    counter = 0
    for sub in submissions:
        submissions_for_threads[counter % num_threads].append(sub)
        counter += 1

    for i in range(len(submissions_for_threads)):
        print(
            f"  Thread-{i+1} will fetch {len(submissions_for_threads[i])} submissions"
        )

    # Create a list to hold the threads
    threads = []

    with ProgressBar(
        max_value=total,
        color="BLUE",
        length=80,
        additional_text="Retrieving codes from user...",
    ) as progress:
        for i in range(num_threads):
            thread_submissions = submissions_for_threads[i]

            thread = CodeFetchingThread(
                f"Thread-{i+1}",
                user,
                thread_submissions,
                progress,
                data["exportfolder"],
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


class Module:
    name = "Submit scraper"
    description = "Scrape submits from sio2"

    def __init__(self, data: dict, user: User, sio2url: str):
        self.data = data
        self.user = user
        self.sio2url = sio2url

    def execute(self):
        print("Got data:", self.data)
        contests, submissions = get_submissions_list(self.user, self.data)
        # print("\n".join(str(x) for x in submissions))
        print("Pre-fetched", len(submissions), "submissions")

        print("Writing data to submissions.txt")
        with open("submissions.txt", "w") as f:
            for submission in submissions:
                f.write(str(submission) + "\n")

        print("DONE")
        print("Fetching code for each submission...")
        fetch_code_all(self.data, self.user, submissions, contests)
