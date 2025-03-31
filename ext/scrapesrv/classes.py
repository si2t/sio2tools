import json

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
        