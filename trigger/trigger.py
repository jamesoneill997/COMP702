import requests
app_url = "https://oddsgenie-scheduler-v1-bva58.ondigitalocean.app/launch"
r = requests.get(app_url)

print(r.status_code)