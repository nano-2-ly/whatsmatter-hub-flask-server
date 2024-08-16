import schedule
import time
import requests
import json
import threading
from datetime import datetime





class one_time_schedule():

    def __init__(self):
        self.one_time_schedule_list = []

    def add_schedule(self, s):
        self.one_time_schedule_list.append(s)

    def run_pending(self):
        for s in self.one_time_schedule_list:
            target_time = datetime.strptime(s['schedule']['datetime'], "%Y-%m-%d %H:%M")
            current_time = datetime.now()
            current_time = current_time.replace(second=0, microsecond=0)

            if current_time < target_time:
                pass
            elif current_time > target_time:
                pass
            else:
                service(s['condition'], s['action']['domain'], s['action']['service'], s['action']['entity'])
            



def checkCondition(condition):
    for c in condition:
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}

        response = requests.get(f"http://192.168.1.195:8123/api/states/{c['entity']}", headers=headers)
        response = json.loads(response.content)

        if(c['option']==""):
            if (response['state'] == c['state']):
                pass
            else : 
                return False
        if(c['option']=="equal"):
            if (response['state'] == c['state']):
                pass
            else : 
                return False
    
    return True


def service(condition, domain, service, entity):
    if (checkCondition(condition)):
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
        body = {"entity_id": entity}

        response = requests.post(f"http://192.168.1.195:8123/api/services/{domain}/{service}", data=json.dumps(body), headers=headers)
        print(response)
        print(response.content)



def schedule_config(one_time):
    schedule.clear()

    with open('resources/schedule.json', 'r', encoding='utf-8') as file:
        data = json.load(file)  # JSON 파일을 파싱하여 Python 객체로 변환
        for _schedule_data in data:
            if(_schedule_data['schedule']['type'] == "periodic"):
                if(_schedule_data['schedule']['period']['rate'] == "seconds"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).seconds.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).seconds.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "minutes"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).minutes.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).minutes.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "hours"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).hours.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).hours.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "days"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).days.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).days.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "weeks"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).weeks.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).weeks.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "monday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).monday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).monday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "tuesday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).tuesday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).tuesday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "wednesday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).wednesday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).wednesday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "thursday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).thursday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).thursday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "friday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).friday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).friday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "saturday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).saturday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).saturday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                if(_schedule_data['schedule']['period']['rate'] == "sunday"):
                    if(_schedule_data['schedule']['period']['at'] != ""):
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).sunday.at(_schedule_data['schedule']['period']['at']).do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])
                    else:
                        schedule.every(int(_schedule_data['schedule']['period']['value'])).sunday.do(service, _schedule_data['condition'], _schedule_data['action']['domain'], _schedule_data['action']['service'], _schedule_data['action']['entity'])


            if(_schedule_data['schedule']['type'] == "one_time"):
                one_time.add_schedule(_schedule_data)

def periodic_scheduler():
    while 1:
        schedule.run_pending()
        time.sleep(1)

def one_time_scheduler(one_time):
    
    while 1:
        one_time.run_pending()
        time.sleep(60)


################# start ##################

if (__name__ == "__main__"):
    one_time = one_time_schedule()

    

    schedule_config(one_time)
    p = threading.Thread(target=periodic_scheduler)
    p.start()
    o = threading.Thread(target=one_time_scheduler, args=one_time)
    o.start()

