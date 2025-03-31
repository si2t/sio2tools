from user import User
import os
import subprocess

class Module:
    name = "Scraper Backend Server"
    description = "Set up a server that logs some useful things from sio2 contests"
    
    def __init__(self, data: dict, user: User):
        self.data = data
        self.user = user
        
    def execute(self):
        print("Starting scraping server...")
        subprocess.run(["uvicorn", f"sio2tools.ext.scrapesrv.main:app", "--port", "8080"])