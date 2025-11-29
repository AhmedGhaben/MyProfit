import credentials
from ctrader_open_api import Auth, Client

auth = Auth(credentials.CLIENT_ID, credentials.CLIENT_SECRET, credentials.REDIRECT_URI)

print(auth.getAuthUri())

auth_code = input("Auth code: ")
tokens = auth.getToken(auth_code)
access_token = tokens['access_token']

print("Access token:", access_token)

client = Client(
    app_id=credentials.CLIENT_ID,
    access_token=access_token,
    account_id=credentials.ACCOUNT_ID
)

client.connect()
print("Connected")