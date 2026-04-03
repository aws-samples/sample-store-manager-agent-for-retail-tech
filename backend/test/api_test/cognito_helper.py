import os
import json
import boto3
from typing import Dict

cognito_client = boto3.client("cognito-idp")


def cognito_first(
    username: str,
    email: str,
    initial_password: str,
    new_password: str,
    user_pool_id: str,
    client_id: str,
) -> Dict[str, str]:
    try:
        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            TemporaryPassword=initial_password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "True"},
            ],
            MessageAction="SUPPRESS",
        )

        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": initial_password},
        )

        challenge_response = cognito_client.admin_respond_to_auth_challenge(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            ChallengeName="NEW_PASSWORD_REQUIRED",
            ChallengeResponses={"USERNAME": username, "NEW_PASSWORD": new_password},
            Session=auth_response["Session"],
        )

        data_token = challenge_response["AuthenticationResult"]
        id_token = data_token["IdToken"]
        refresh_token = data_token["RefreshToken"]

        with open(".env", "w") as f:
            f.write(f"COGNITO_ID_TOKEN={id_token}\n")
            f.write(f"COGNITO_REFRESH_TOKEN={refresh_token}\n")

        return {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

    except cognito_client.exceptions.UsernameExistsException:
        auth_response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": new_password},
        )

        id_token = auth_response["AuthenticationResult"]["IdToken"]
        refresh_token = auth_response["AuthenticationResult"]["RefreshToken"]

        with open(".env", "w") as f:
            f.write(f"COGNITO_ID_TOKEN={id_token}\n")
            f.write(f"COGNITO_REFRESH_TOKEN={refresh_token}\n")

        return {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }


def cognito_second(user_pool_id: str, client_id: str) -> Dict[str, str]:
    if not os.path.exists(".env"):
        raise FileNotFoundError(".env file not found. Run cognito_first() first.")

    with open(".env", "r") as f:
        env_content = f.read()

    refresh_token = None
    for line in env_content.split("\n"):
        if line.startswith("COGNITO_REFRESH_TOKEN="):
            refresh_token = line.split("=", 1)[1]
            break

    if not refresh_token:
        raise ValueError("COGNITO_REFRESH_TOKEN not found in .env file")

    try:
        response = cognito_client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )

        id_token = response["AuthenticationResult"]["IdToken"]

        with open(".env", "r") as f:
            lines = f.readlines()

        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("COGNITO_ID_TOKEN="):
                    f.write(f"COGNITO_ID_TOKEN={id_token}\n")
                else:
                    f.write(line)

        return {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }

    except Exception as e:
        print(f"Failed to refresh token: {str(e)}")
        with open(".env", "r") as f:
            env_content = f.read()

        id_token = None
        for line in env_content.split("\n"):
            if line.startswith("COGNITO_ID_TOKEN="):
                id_token = line.split("=", 1)[1]
                break

        if not id_token:
            raise ValueError("COGNITO_ID_TOKEN not found in .env file")

        return {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }


def get_auth_headers(local_mode: bool = True) -> Dict[str, str]:
    if local_mode:
        return {"Content-Type": "application/json"}

    username = os.environ.get("AUTH_USERNAME")
    password = os.environ.get("AUTH_PASSWORD")
    user_pool_id = os.environ.get("USER_POOL_ID")
    client_id = os.environ.get("USER_POOL_CLIENT_ID")

    if not all([username, password, user_pool_id, client_id]):
        raise ValueError(
            "Missing required environment variables: AUTH_USERNAME, AUTH_PASSWORD, USER_POOL_ID, USER_POOL_CLIENT_ID"
        )

    if not os.path.exists(".env"):
        return cognito_first(
            username, username, password, password, user_pool_id, client_id
        )
    else:
        return cognito_second(user_pool_id, client_id)
