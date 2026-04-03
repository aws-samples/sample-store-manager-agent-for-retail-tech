import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as s3tables from 'aws-cdk-lib/aws-s3tables';
import { Construct } from 'constructs';
import * as path from 'path';

export class DataResourcesConstruct extends Construct {
  public readonly dataSourceBucket: s3.Bucket;
  public readonly tableBucket: s3tables.CfnTableBucket;
  public readonly namespace: s3tables.CfnNamespace;
  public readonly athenaResultsBucket: s3.Bucket;
  public readonly promptBucket: s3.Bucket;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    const stack = cdk.Stack.of(this);

    this.dataSourceBucket = new s3.Bucket(this, 'DataSourceBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: false,
      enforceSSL: true,
    });

    this.tableBucket = new s3tables.CfnTableBucket(this, 'TableBucket', {
      tableBucketName: `s3tables-store-data-${stack.account}-${stack.region}`,
      unreferencedFileRemoval: {
        status: 'Enabled',
        unreferencedDays: 7,
      },
    });

    this.namespace = new s3tables.CfnNamespace(this, 'Namespace', {
      namespace: 'store_data',
      tableBucketArn: this.tableBucket.attrTableBucketArn,
    });

    this.athenaResultsBucket = new s3.Bucket(this, 'AthenaResultsBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: false,
      enforceSSL: true,
    });

    this.promptBucket = new s3.Bucket(this, 'PromptBucket', {
      bucketName: `store-manager-agent-prompts-${stack.account}-${stack.region}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      publicReadAccess: false,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      autoDeleteObjects: false,
      enforceSSL: true,
    });

    new s3deploy.BucketDeployment(this, 'DeployPrompts', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../../../cdk/prompt'))],
      destinationBucket: this.promptBucket,
      destinationKeyPrefix: 'prompt/',
    });
  }
}
