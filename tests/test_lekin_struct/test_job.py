from datetime import datetime


class Job:
    def __init__(
        self,
        id,
        earliest_breach_date=None,
        earliest_promised_date=None,
        earliest_latest_completion_time=None,
        required_date=None,
    ):
        self.id = id
        self.earliest_breach_date = earliest_breach_date
        self.earliest_promised_date = earliest_promised_date
        self.earliest_latest_completion_time = earliest_latest_completion_time
        self.required_date = required_date


a = Job(id=0, earliest_breach_date=datetime(2022, 9, 1))

b = Job(id=1, earliest_promised_date=datetime(2022, 8, 1))

c = Job(id=2, earliest_breach_date=datetime(2022, 9, 10))

d = Job(id=3, earliest_promised_date=datetime(2022, 9, 5))

e = Job(id=4, required_date=datetime(2022, 7, 5))

candidates = [a, b, c, d, e, a]

candidates = sorted(
    candidates,
    key=lambda x: (
        x.earliest_breach_date is None,
        x.earliest_breach_date,
        x.earliest_promised_date is None,
        x.earliest_promised_date,
        x.earliest_latest_completion_time is None,
        x.earliest_latest_completion_time,
        x.required_date,
    ),
)
print([i.id for i in candidates])
