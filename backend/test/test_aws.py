#!/usr/bin/env python3
"""
AWS API Gateway test runner for Store Daily QA System
Executes tests against deployed API Gateway endpoint
"""

import sys
import subprocess
from pathlib import Path
import argparse
import os
import json

sys.path.insert(0, str(Path(__file__).parent / "api_test"))
from cognito_helper import cognito_first, cognito_second


def load_cdk_outputs():
    """Load CDK outputs"""
    cdk_outputs_path = Path(__file__).parent.parent.parent / "cdk" / ".cdk-outputs.json"

    if not cdk_outputs_path.exists():
        print(f"❌ CDK outputs file not found: {cdk_outputs_path}")
        print("Please deploy the CDK stack first:")
        print("  cd cdk")
        print("  cdk deploy")
        return None

    with open(cdk_outputs_path, "r") as f:
        outputs = json.load(f)

    return outputs.get("BackendStack", {})


def setup_environment():
    """Setup environment variables from CDK outputs"""
    cdk_outputs = load_cdk_outputs()
    if not cdk_outputs:
        return None

    api_url = cdk_outputs.get("ApiLambdaApiEndpoint217CF83B") or cdk_outputs.get(
        "ApiLambdaApiUrl7A2B82FF"
    )

    if not api_url:
        print("❌ API Gateway URL not found in CDK outputs")
        print("Expected keys: ApiLambdaApiEndpoint217CF83B or ApiLambdaApiUrl7A2B82FF")
        return None

    os.environ["TABLE_BUCKET_ARN"] = cdk_outputs["TableBucketArn"]
    os.environ["ATHENA_OUTPUT_LOCATION"] = cdk_outputs["AthenaOutputLocation"]

    return api_url


def run_api_tests(test_module=None, verbose=False, exclude_agent=False):
    """Run API tests"""
    api_test_script = Path(__file__).parent / "api_test" / "api_test_local.py"

    cmd = ["python", str(api_test_script)]

    if test_module:
        cmd.extend(["--module", test_module])

    if verbose:
        cmd.append("--verbose")

    if exclude_agent:
        cmd.append("--exclude-agent")

    print(f"🧪 Running API tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AWS API Gateway Test Runner")
    parser.add_argument(
        "--module",
        choices=[
            "admin",
            "survey",
            "chat",
            "insights",
            "admin_errors",
            "survey_errors",
            "insights_errors",
            "agent",
        ],
        help="Run tests for specific module only",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--user", help="Cognito user email address")
    parser.add_argument("--pass", dest="password", help="Cognito user password")
    parser.add_argument(
        "--first",
        action="store_true",
        help="First time execution - create Cognito user",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AWS API Gateway Test Runner")
    print("=" * 60)

    api_url = setup_environment()
    if not api_url:
        return 1

    print(f"✅ API Gateway URL: {api_url}")
    print("✅ Environment configuration loaded from CDK outputs")
    os.environ["API_BASE_URL"] = api_url.rstrip("/")

    if args.user and args.password:
        cdk_outputs = load_cdk_outputs()
        if not cdk_outputs:
            return 1

        user_pool_id = cdk_outputs.get("UserPoolId")
        user_pool_client_id = cdk_outputs.get("UserPoolClientId")

        if not user_pool_id or not user_pool_client_id:
            print("❌ Cognito configuration not found in CDK outputs")
            print("Expected keys: UserPoolId, UserPoolClientId")
            return 1

        print(f"✅ Cognito User Pool ID: {user_pool_id}")
        print(f"✅ Cognito Client ID: {user_pool_client_id}")

        try:
            if args.first:
                print("🔐 Creating Cognito user and obtaining token...")
                auth_headers = cognito_first(
                    args.user,
                    args.user,
                    args.password,
                    args.password,
                    user_pool_id,
                    user_pool_client_id,
                )
            else:
                print("🔐 Refreshing Cognito token...")
                auth_headers = cognito_second(user_pool_id, user_pool_client_id)

            os.environ["COGNITO_AUTH_HEADER"] = auth_headers.get("Authorization", "")
            print("✅ Cognito authentication successful")
        except Exception as e:
            print(f"❌ Cognito authentication failed: {str(e)}")
            return 1
    else:
        print(
            "⚠️  No Cognito credentials provided - tests will run without authentication"
        )

    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    exclude_agent = args.module != "agent" if args.module else True

    exit_code = run_api_tests(args.module, args.verbose, exclude_agent)

    print("-" * 60)

    if exit_code == 0:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n💥 Some tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
