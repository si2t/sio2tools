class Submission:
    def __init__(
        self,
        name: str = None,
        points: int = None,
        status: str = None,
        submission_time: str = None,
        url: str = None,
        contest_id: str = None,
    ):
        self.name: str = name
        self.points: int = points
        self.status: str = status
        self.submission_time: str = submission_time
        self.url: str = url
        self.contest_id: str = contest_id

    @property
    def id(self):
        if not self.url:
            return None
        return self.url.split("/")[-2]

    def __str__(self):
        return f"{self.name} - {self.points} - {self.status} - {self.submission_time} - {self.id}"

class Round:
    def __init__(
        self,
        name: str,
        date_range: str
    ):
        self.name: str = name
        self.date_range: str = date_range

class Problem:
    def __init__(
        self,
        name: str,
        short_code: str,
        user_points: int | None,
        url: str,
        submissions_status: str,
        best_solution_sub_url: str,
        round: Round,
    ):
        self.name: str = name
        self.short_code: str = short_code
        self.user_points: int | None = user_points
        self.url: str = url
        self.submissions_status: str = submissions_status
        self.best_solution_sub_url: str = best_solution_sub_url
        self.round: Round = round