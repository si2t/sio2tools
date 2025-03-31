import importlib, os
from colorama import Fore, Style
import colorama
import traceback
from user import User
from bs4 import BeautifulSoup
import requests
import sio2submit

colorama.init(autoreset=True)
SIO2_BASEURL = "https://wyzwania.programuj.edu.pl/"


def parse_data(data):
    if data is None:
        return None

    data = data.strip().split(";")
    res = {}
    for x in data:
        x = x.split("=")
        if len(x) != 2:
            continue
        res[x[0].strip()] = x[1].strip()

    return res

def can_module_ignore_user(module_name):
    module_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "modules", module_name
    )
    try:
        module = importlib.import_module("modules." + module_name)

        if not hasattr(module, "Module"):
            raise AttributeError(
                "Invalid Extension: Module class not found in extension"
            )

        cls = module.Module
        if hasattr(cls, "can_ignore_user"):
            return cls.can_ignore_user
        else:
            return False
    except:
        pass

def execute_module(extension_name, data, user, sio2url):
    module_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "modules", extension_name
    )
    print("Loading module " + Fore.MAGENTA + str(module_path) + Style.RESET_ALL + "...")
    try:
        module = importlib.import_module("modules." + extension_name)

        if not hasattr(module, "Module"):
            raise AttributeError(
                "Invalid Extension: Module class not found in extension"
            )

        instance = module.Module(parse_data(data), user, sio2url)
        print("  Detected instance Module", instance.name, ":", instance.description)
        print("  Executing...")
        instance.execute()
    except Exception as e:
        print(
            "An error occurred while loading/executing the extension",
            extension_name,
            ":",
        )
        if isinstance(e, ModuleNotFoundError):
            print(Fore.RED + "  Module " + extension_name + " not found")
            return

        print("More information:")
        colorama.init(autoreset=False)
        print(Fore.RED + traceback.format_exc())
        print(Style.RESET_ALL + "------ END -----")
        colorama.init(autoreset=True)

def get_contest_names(user: User, return_ids=True, return_names=True):
    contest_pages = user.fetch_sio2("contest/").text
    soup = BeautifulSoup(contest_pages, "html.parser")
    table = soup.find("table", {"class": "table"}).find("tbody")
    contest_containers = table.find_all("tr")
    
    res = []
    for contest in contest_containers:
        contest_id, contest_name = contest.find_all("td")
        contest_id = contest_id.text.strip()
        contest_name = contest_name.text.strip()
        
        cur = []
        if return_ids:
            cur.append(contest_id)
        if return_names:
            cur.append(contest_name)
        
        res.append(tuple(cur))
    
    return res
    

def datatable(datalist: list, headers: list, colored: bool = True):
    col_widths = [len(str(x)) for x in headers]
    fore = Fore.MAGENTA if colored else ""
    
    for x in datalist:
        for i, e in enumerate(x):
            col_widths[i] = max(col_widths[i], len(str(e)))
        
    # print headers using join
    print(f" {fore}|{Style.RESET_ALL} ".join([Fore.MAGENTA + Style.BRIGHT + str(x).ljust(col_widths[i]) + Style.RESET_ALL for i, x in enumerate(headers)]))
    print(fore + "|".join("=" * (cw+2 if i != 0 else cw+1) for i, cw in enumerate(col_widths)))
    # print table body
    for x in datalist:
        print(f" {fore}|{Style.RESET_ALL} ".join([str(x).ljust(col_widths[i]) for i, x in enumerate(x)]))

def submit_solution(token: str, url: str, task: str, file: str, webbrowser: bool):
    print("submit_solution got these paremeters:", "token", token, "url", url, "task", task, "file", file, "webb", webbrowser)
    sio2submit.submit(file, task, token, url, webbrowser)

def list_extensions():
    print("Available modules for SIO2 Tools:")
    print("==================================")
    module_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "modules")
    i = 1
    for file_name in os.listdir(module_folder):
        if file_name == "__pycache__":
            continue
        print(str(i) + ". " + file_name[:-3])
        i += 1
