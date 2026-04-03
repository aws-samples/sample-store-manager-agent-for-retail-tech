import json
import os
import boto3

cognito_client = boto3.client("cognito-idp")


def handler(event, context):
    user_pool_id = os.environ.get("USER_POOL_ID")
    auto_join_groups_str = os.environ.get("AUTO_JOIN_USER_GROUPS_STR", "[]")
    auto_join_groups = json.loads(auto_join_groups_str)

    if not auto_join_groups:
        return event

    username = event["userName"]

    for group_name in auto_join_groups:
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=user_pool_id, Username=username, GroupName=group_name
            )
        except Exception as e:
            print(f"Failed to add user to group {group_name}: {str(e)}")

    return event
