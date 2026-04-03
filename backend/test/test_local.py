#!/usr/bin/env python3
"""
Main test runner for Store Daily QA System
Manages Docker Compose and executes API tests
"""

import sys
import subprocess
from pathlib import Path
import argparse
import os
import time
import json


def load_cdk_outputs():
    """Load CDK outputs from .cdk-outputs.json"""
    cdk_outputs_path = Path(__file__).parent.parent.parent / "cdk" / ".cdk-outputs.json"
    with open(cdk_outputs_path) as f:
        outputs = json.load(f)
    return outputs["BackendStack"]


def prepare_docker_env():
    """Prepare environment variables for Docker from CDK outputs"""
    cdk_outputs = load_cdk_outputs()

    env = os.environ.copy()

    runtime_arn = cdk_outputs["AgentCoreRuntimeArn"]
    region = runtime_arn.split(":")[3]

    env.update(
        {
            "TABLE_BUCKET_ARN": cdk_outputs["TableBucketArn"],
            "NAMESPACE": cdk_outputs["NamespaceName"],
            "ATHENA_OUTPUT_LOCATION": cdk_outputs["AthenaOutputLocation"],
            "ATHENA_WORKGROUP": cdk_outputs["AthenaWorkgroup"],
            "REGION": region,
            "AGENTCORE_RUNTIME_ARN": runtime_arn,
            "AGENTCORE_REGION": region,
            "HEARING_AGENTCORE_MEMORY_ID": cdk_outputs["HearingMemoryId"],
            "DAILY_SUMMARY_AGENTCORE_MEMORY_ID": cdk_outputs["DailySummaryMemoryId"],
        }
    )

    return env


def start_docker_services():
    """Start Docker Compose services"""
    env = prepare_docker_env()

    print("🐳 Building Docker images...")
    build_result = subprocess.run(
        ["docker-compose", "build"], capture_output=True, text=True, env=env
    )
    if build_result.returncode != 0:
        print(f"❌ Failed to build Docker images: {build_result.stderr}")
        return False

    print("🐳 Starting Docker services...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"], capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        print(f"❌ Failed to start Docker services: {result.stderr}")
        return False

    print("⏳ Waiting for services to be ready...")
    max_retries = 30
    for i in range(max_retries):
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            env=env,
        )
        if "healthy" in result.stdout:
            print("✅ Services are ready!")
            return True
        time.sleep(2)
        print(f"   Waiting... ({i + 1}/{max_retries})")

    print("❌ Services failed to become healthy")
    return False


def stop_docker_services():
    """Stop Docker Compose services"""
    print("🛑 Stopping Docker services...")
    subprocess.run(["docker-compose", "down"], capture_output=True)
    print("✅ Services stopped")


def run_api_tests(test_module=None, verbose=False, exclude_agent=False):
    """Run API tests by calling api_test_local.py"""
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
    parser = argparse.ArgumentParser(description="Store Daily QA System Test Runner")
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

    args = parser.parse_args()

    print("=" * 60)
    print("Store Daily QA System Test Runner")
    print("=" * 60)

    required_env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required AWS credentials: {', '.join(missing_vars)}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}=<your-value>")
        return 1

    print("✅ AWS credentials found")

    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    exit_code = 0

    try:
        if not start_docker_services():
            return 1

        exclude_agent = args.module != "agent" if args.module else True

        exit_code = run_api_tests(args.module, args.verbose, exclude_agent)

    finally:
        print("-" * 60)

    if exit_code == 0:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n💥 Some tests failed!")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
