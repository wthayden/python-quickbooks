from flask import Flask, request, redirect, url_for
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from quickbooks import QuickBooks

app = Flask(__name__)

# Your QuickBooks app credentials
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'http://localhost:5000/callback'
ENVIRONMENT = 'sandbox'  # or 'production'

auth_client = AuthClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    environment=ENVIRONMENT,
    redirect_uri=REDIRECT_URI,
)

@app.route('/')
def index():
    auth_url = auth_client.get_authorization_url([
        Scopes.ACCOUNTING,
    ])
    return f'<a href="{auth_url}">Connect to QuickBooks</a>'

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    realm_id = request.args.get('realmId')
    
    # Exchange auth code for tokens
    auth_client.get_bearer_token(auth_code, realm_id=realm_id)
    
    # Create QuickBooks client
    client = QuickBooks(
        auth_client=auth_client,
        refresh_token=auth_client.refresh_token,
        company_id=realm_id,
    )

    return f"""
    Access Token: {auth_client.access_token}<br>
    Refresh Token: {auth_client.refresh_token}<br>
    Realm ID: {realm_id}
    """

if __name__ == '__main__':
    app.run(debug=True, port=5000)