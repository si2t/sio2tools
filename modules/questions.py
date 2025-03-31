from user import User

class Module:
    name = "Questions and Answers module"
    description = "Ask questions and answer on the contest forum"
    
    def __init__(self, data: dict, user: User, sio2url: str):
        self.data = data
        self.user = user
        self.sio2url = sio2url
        
    def execute(self):
        print("Executing Questions and Answers module")
        print("Data:", self.data)
        print("User:", self.user)