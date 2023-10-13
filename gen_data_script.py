import json
import requests
import hashlib
import hmac
import time
import base64
import datetime

SERVER_API_URL = 'http://localhost:8080'
APP_NAME = 'test_app'
APP_KEY = 'test_key'


def get_hmac_header(method, path, body):
    window = int(time.time()) // 5
    text = f"{window} {method} {path} {body}"
    hashed = hmac.new(APP_KEY.encode(), text.encode('utf-8'), hashlib.sha512)
    signature = base64.urlsafe_b64encode(hashed.digest()).decode('utf-8')
    return f"hmac {APP_NAME}:{signature}"


def make_api_post(url, data):
    body = json.dumps(data)
    auth = get_hmac_header('POST', url, body)
    res = requests.post(f'{SERVER_API_URL}{url}', json=data, headers={'AUTHORIZATION': auth})
    return res.text


def make_api_put(url, data):
    body = json.dumps(data)
    auth = get_hmac_header('PUT', url, body)
    res = requests.put(f'{SERVER_API_URL}{url}', json=data, headers={'AUTHORIZATION': auth})
    return res.text


def create_team(team_name, tz, email, slack):
    data = {
        "name": team_name,
        "scheduling_timezone": tz,
        "email": email,
        "slack_channel": slack,
        "admin": 'root'
    }
    return make_api_post('/api/v0/teams', data)


def create_user(name, full_name, phone_number, email):
    data = {
        "name": name,
    }
    print(make_api_post('/api/v0/users', data))
    return make_api_put(f'/api/v0/users/{name}', {
        "contacts": {
            "call": phone_number,
            "email": email,
            "sms": phone_number
        },
        "full_name": full_name
    })


def create_roster(team, name):
    return make_api_post(f'/api/v0/teams/{team}/rosters', {"name": name})


def add_user_to_team_roster(team, user, roster_name):
    return make_api_post(f'/api/v0/teams/{team}/rosters/{roster_name}/users', {"name": user})


def create_event(team, user, role, date):
    datet = datetime.datetime.strptime(date, '%d/%m/%Y')
    start = time.mktime(datet.timetuple())
    end = start + 86400.0
    data = {
        "start": start,
        "end": end,
        "team": team,
        "user": user,
        "role": role,
    }
    return make_api_post('/api/v0/events', data)


# Create teams
print(create_team('k8s SRE', 'Europe/Moscow', 'k8s@sre-course.ru', '#k8s-team'))
print(create_team('DBA SRE', 'Asia/Novosibirsk', 'dba@sre-course.ru', '#dba-team'))

# Create users
print(create_user('o.ivanov', 'Oleg Ivanov', '+1 111-111-1111', 'o.ivanov@sre-course.ru'))
print(create_user('d.petrov', 'Dmitriy Petrov', '+1 211-111-1111', 'd.petrov@sre-course.ru'))
print(create_user('a.seledkov', 'Alexander Seledkov', '+1 311-111-1111', 'a.seledkov@sre-course.ru'))
print(create_user('d.hludeev', 'Dmitriy Hludeev', '+1 411-111-1111', 'user-4@sre-course.ru'))

# Create roster to add users in team
print(create_roster('DBA SRE', 'duty'))
print(create_roster('k8s SRE', 'duty'))

# Add users in team
print(add_user_to_team_roster('DBA SRE', 'a.seledkov', 'duty'))
print(add_user_to_team_roster('DBA SRE', 'd.hludeev', 'duty'))

print(add_user_to_team_roster('k8s SRE', 'o.ivanov', 'duty'))
print(add_user_to_team_roster('k8s SRE', 'd.petrov', 'duty'))

# Create users events
print(create_event('DBA SRE', 'a.seledkov', 'primary', '02/10/2023'))
print(create_event('DBA SRE', 'a.seledkov', 'primary', '03/10/2023'))
print(create_event('DBA SRE', 'a.seledkov', 'primary', '04/10/2023'))
print(create_event('DBA SRE', 'a.seledkov', 'secondary', '05/10/2023'))
print(create_event('DBA SRE', 'a.seledkov', 'primary', '06/10/2023'))

print(create_event('DBA SRE', 'd.hludeev', 'secondary', '02/10/2023'))
print(create_event('DBA SRE', 'd.hludeev', 'secondary', '03/10/2023'))
print(create_event('DBA SRE', 'd.hludeev', 'vacation', '04/10/2023'))
print(create_event('DBA SRE', 'd.hludeev', 'primary', '05/10/2023'))
print(create_event('DBA SRE', 'd.hludeev', 'secondary', '06/10/2023'))

print(create_event('k8s SRE', 'o.ivanov', 'primary', '02/10/2023'))
print(create_event('k8s SRE', 'o.ivanov', 'secondary', '03/10/2023'))
print(create_event('k8s SRE', 'o.ivanov', 'primary', '04/10/2023'))
print(create_event('k8s SRE', 'o.ivanov', 'secondary', '05/10/2023'))
print(create_event('k8s SRE', 'o.ivanov', 'primary', '06/10/2023'))

print(create_event('k8s SRE', 'd.petrov', 'secondary', '02/10/2023'))
print(create_event('k8s SRE', 'd.petrov', 'primary', '03/10/2023'))
print(create_event('k8s SRE', 'd.petrov', 'secondary', '04/10/2023'))
print(create_event('k8s SRE', 'd.petrov', 'primary', '05/10/2023'))
print(create_event('k8s SRE', 'd.petrov', 'secondary', '06/10/2023'))
