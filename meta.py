from datetime import datetime
class Status:
    def __init__(self):
        self.NEW = 'new'
        self.DONE = 'done'
status = Status()

d = datetime.now()
CoWIN_URL = f'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode=@pincode&date={d.day}-{d.month}-2021'
