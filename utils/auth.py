import urllib
import requests

def get_authorization_url(app_url, client_id):
    """Generate authorization uri"""
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": app_url,
        "scope": "read,profile:read_all,activity:read",
        "approval_prompt": "force"
    }
    values_url = urllib.parse.urlencode(params)
    base_url = 'https://www.strava.com/oauth/authorize'
    rv = base_url + '?' + values_url
    return rv

# @st.cache_data(ttl=600, show_spinner=False)
def request_access_token(client_id, client_secret, refresh_token):
    """
    Post request to refresh and get new API access token

    Parameters:
        client_id: string
        client_secret: string
        refresh_token: string
    
    Returns:
        access_token: string
    """
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': refresh_token,
        'grant_type': 'authorization_code',
        'f': 'json'
    }
    print("\nRequesting Access Token...")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()
    return access_token