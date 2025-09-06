# generate_token.py

import os
import pickle
import base64
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes define the level of access you are requesting.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
CLIENT_SECRETS_FILE = 'client_secret.json'
TOKEN_PICKLE_FILE = 'token.pickle'

def generate_local_token():
    """
    Runs the OAuth 2.0 flow to generate a token.pickle file for local development.
    """
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"Error: '{CLIENT_SECRETS_FILE}' not found.")
        print("Please download your OAuth 2.0 credentials from Google Cloud Console and save it as client_secret.json.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    print("\nYour web browser will now open for you to authorize the application.")
    credentials = flow.run_local_server(port=0)

    with open(TOKEN_PICKLE_FILE, 'wb') as token_file:
        pickle.dump(credentials, token_file)

    print(f"\n✅ Authorization complete! '{TOKEN_PICKLE_FILE}' has been created successfully.")
    print("You can now run the main application locally.")

def encode_secrets_for_deployment():
    """
    Encodes client_secret.json and token.pickle into base64 strings for deployment.
    """
    if not all(os.path.exists(f) for f in [CLIENT_SECRETS_FILE, TOKEN_PICKLE_FILE]):
        print(f"\nError: Make sure both '{CLIENT_SECRETS_FILE}' and '{TOKEN_PICKLE_FILE}' exist.")
        print(f"If you don't have '{TOKEN_PICKLE_FILE}', run 'python generate_token.py' first to create it.")
        return

    # Encode client_secret.json
    with open(CLIENT_SECRETS_FILE, "rb") as f:
        client_secret_b64 = base64.b64encode(f.read()).decode('utf-8')

    # Encode token.pickle
    with open(TOKEN_PICKLE_FILE, "rb") as f:
        token_pickle_b64 = base64.b64encode(f.read()).decode('utf-8')

    print("\n🚀 Copy these secrets and paste them into your deployment platform's secrets manager (e.g., Streamlit Cloud secrets):\n")
    print("="*80)
    print("CLIENT_SECRET_B64:")
    print(client_secret_b64)
    print("\nTOKEN_PICKLE_B64:")
    print(token_pickle_b64)
    print("="*80)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate YouTube API token or encode secrets for deployment.")
    parser.add_argument(
        '--encode',
        action='store_true',
        help="Encode existing secret files into base64 strings for deployment."
    )
    args = parser.parse_args()

    if args.encode:
        encode_secrets_for_deployment()
    else:
        generate_local_token()