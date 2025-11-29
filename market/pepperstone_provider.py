import credentials_pepperstone
from ctrader_open_api import Auth, Client

auth = Auth(credentials_pepperstone.CLIENT_ID, credentials_pepperstone.CLIENT_SECRET, credentials_pepperstone.REDIRECT_URI)

print(auth.getAuthUri())

auth_code = input("Auth code: ")
tokens = auth.getToken(auth_code)
access_token = tokens['access_token']

print("Access token:", access_token)

client = Client(
    app_id=credentials_pepperstone.CLIENT_ID,
    access_token=access_token,
    account_id=credentials_pepperstone.ACCOUNT_ID
)

client.connect()
print("Connected")