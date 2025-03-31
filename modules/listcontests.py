from user import User
from utils import get_contest_names, datatable

class Module:
    name = "List Contests"
    description = "List all contests available for this user"
    
    def __init__(self, data: dict, user: User, sio2url: str):
        self.user = user
        self.data = data
        self.sio2url = sio2url
        
    def execute(self):
        print("\nFetching contests...")
        
        # get contest list
        fetched_contests = get_contest_names(self.user)
                
        print("Found", len(fetched_contests), "contests")
        datatable(list([(i, a, b) for (i, (a, b)) in enumerate(fetched_contests, start=1)]), ["#", "ID", "Name"])