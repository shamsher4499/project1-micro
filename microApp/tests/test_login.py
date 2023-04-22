import requests
import json

endpoints = 'http://localhost/api/v1/auth/login/'

headersList = {
 "Accept": "*/*",
 "User-Agent": "Thunder Client (https://www.thunderclient.com)",
 "Content-Type": "application/json" 
}

payload = json.dumps({
  "email":"store13@getnada.com",
  "mobile":"None",
  "password":"12345",
  "fcm_token":"sfsdfsdf-sdfsdff"
})


def test_login():
    response = requests.request("POST", endpoints, data=payload,  headers=headersList)
    assert json.loads(response.text)['status'] == False

# test_login() 