import urllib
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_authorization_url(app_url, client_id):
    """
    Creates authorization url for use in Strava OAuth 

    Parameters:
        app_url: String
        client_id: String
    
    Returns:
        auth_url: String
    """
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": app_url,
        "scope": "read,profile:read_all,activity:read",
        "approval_prompt": "force"
    }
    values_url = urllib.parse.urlencode(params)
    base_url = 'https://www.strava.com/oauth/authorize'
    auth_url = base_url + '?' + values_url
    return auth_url

def request_access_token(client_id, client_secret, auth_code):
    """
    Post request to refresh and get new API access token

    Parameters:
        client_id: String
        client_secret: String
        auth_code: String
    
    Returns:
        access_token: Dict
    """
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'f': 'json'
    }
    print("\nRequesting Access Token...")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()
    return access_token