"""
Generate config.json from CDK outputs
"""

import json
from pathlib import Path


def main():
    # Load CDK outputs
    cdk_outputs_path = Path(__file__).parent.parent / "cdk" / ".cdk-outputs.json"
    with open(cdk_outputs_path, "r") as f:
        cdk_outputs = json.load(f)

    backend_stack = cdk_outputs.get("BackendStack", {})

    # Generate config
    config = {
        "s3": {
            "bucket_name": backend_stack.get("DataSourceBucketName"),
            "prefix": "test-data/",
        },
        "s3_tables": {
            "table_bucket_arn": backend_stack.get("TableBucketArn"),
            "namespace": backend_stack.get("NamespaceName"),
        },
        "temp_catalog": {"database_name": "temp_csv_catalog"},
        "athena": {
            "workgroup": backend_stack.get("AthenaWorkgroup"),
            "output_location": backend_stack.get("AthenaOutputLocation"),
        },
    }

    # Write config.json
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Generated {config_path}")


if __name__ == "__main__":
    main()
