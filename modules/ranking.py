from user import User
from colorama import Style, Fore
from progressbar import ProgressBar, TICK
import bs4
import time
from datetime import datetime
import os

class Module:
    name = "Generate Ranking module"
    description = "Generate ranking based on groups and apply ranking weights"

    def __init__(self, data: dict, user: User, sio2url: str = None):
        self.data = data
        self.user = user
        self.sio2url = sio2url

    def execute(self):
        print("Executing ranking module")
        print(f"{Style.DIM}Data:", self.data)
        browser = self.data.get("browser", "n").lower() in ["y", "tak", "yes", "1"];
        groups = self.data.get("groups", "").split(",")
        title = self.data.get("name", "Ranking")
        savefile = os.path.abspath(self.data.get("saveile", "./ranking_" + title + ".html"))
        # generate group weights
        group_weights = {}
        for g in groups:
            name, wght = g.split(":")
            group_weights[name] = int(wght)

        print(f"{Style.DIM}Ranking name:", title)
        print(f"{Style.DIM}Ranking HTML output path:", savefile)
        print(f"{Style.DIM}Ranking groups:", group_weights)
        print(f"{Style.DIM}Open in webbrowser:", browser)

        num_groups = len(group_weights.values())
        fetched_users = {}
        start = time.time()

        with ProgressBar(max_value=num_groups, color="MAGENTA", length=80, additional_text="Fetching user ranking...") as pb:
            for gr, wght in group_weights.items():
                this_ranking = self.user.fetch_sio2("c/" + gr + "/ranking")
                soup = bs4.BeautifulSoup(this_ranking.text, "html.parser")
                table = soup.find(class_="table table-ranking table-striped table-sm submission").find("tbody").find_all("tr")
                num_users = len(table)

                for i, tr in enumerate(table):
                    tds = tr.find_all("td")
                    user_name = tds[1].text
                    points = int(tds[2].text)
                    try:
                        fetched_users[user_name][gr] = points*wght
                        fetched_users[user_name]["total"] += points*wght
                    except KeyError:
                        fetched_users[user_name] = {}
                        for g in group_weights.keys():
                            fetched_users[user_name][g] = 0
                        fetched_users[user_name][gr] = points*wght
                        fetched_users[user_name]["total"] = points*wght
                pb.update_next(f"{TICK} [{time.time()-start:.2f}s] Fetched data from ranking {Fore.GREEN}{gr} ({wght}){Fore.WHITE} (users: {num_users})")

        sorted_users = sorted(list(fetched_users.items()), key=lambda e: e[1]["total"], reverse=True)

        print("\nRanking: ")
        print("".join(
            f"{Style.DIM}{i}.{Style.RESET_ALL} {Fore.BLUE}{u}{Style.RESET_ALL}: {d['total']} a: {d['a']} b: {d['b']} c: {d['c']} d: {d['d']}\n"
            for i, (u, d) in enumerate(sorted_users, start=1)
        ))

        print("\nGenerating ranking HTML...")
        template_replace = "<!--- {table filling goes here} ---->"
        res = ""
        template_table = """
        <tr>
        <th scope="row">{num}</th>
        <td>{username}</td>
        <td>{total}</td>
        """

        # generate points tables
        for g, w in group_weights.items():
            template_table += "<td>{points_" + g + "} ({points_no_" + g + "})</td>\n"

        template_table += "</tr>"

        def conv_int(idx):
            if idx == 1:
                return "🏆"
            if idx == 2:
                return "🥈"
            if idx == 3:
                return "🥉"
            return str(idx)

        all_res = ""
        for i, (username, data) in enumerate(sorted_users, start=1):
            res = template_table.replace("{num}", conv_int(i)).replace("{username}", username).replace("{total}", str(data["total"]))
            for gr, wght in group_weights.items():
                res = res.replace("{points_" + gr + "}", str(data[gr])).replace("{points_no_" + gr + "}", str(int(data[gr] / wght)))
            all_res += res

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "ranking_template.html"), mode="r", encoding="utf-8") as f:
            content = f.read()

        rep = content.replace("{RANKINGNAME}", title).replace("{GENERATED_TIME}", datetime.now().strftime("%H:%M:%S %d/%m/%Y")).replace(template_replace, all_res)
        with open(savefile, mode="w", encoding="utf-8") as f:
            f.write(rep)

        print(f"{Style.DIM}Saved HTML output to:", savefile)
        if browser:
            print("Attempting to open HTML ranking in browser...")
            print(Fore.RED + "[!] No browser support yet")
            # webbrowser.get(browser).open("file://" + savefile)