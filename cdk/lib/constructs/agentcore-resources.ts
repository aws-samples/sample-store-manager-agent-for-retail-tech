import * as cdk from 'aws-cdk-lib';
import * as agentcore from '@aws-cdk/aws-bedrock-agentcore-alpha';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lakeformation from 'aws-cdk-lib/aws-lakeformation';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import * as path from 'path';
import { Construct } from 'constructs';
import { ContainerImageBuild } from 'deploy-time-build';
import { DataResourcesConstruct } from './data-resources';

export interface AgentCoreResourcesConstructProps {
  dataResources: DataResourcesConstruct;
}

export class AgentCoreResourcesConstruct extends Construct {
  public readonly hearingMemory: agentcore.Memory;
  public readonly dailySummaryMemory: agentcore.Memory;
  public readonly runtime: agentcore.Runtime;

  constructor(scope: Construct, id: string, props: AgentCoreResourcesConstructProps) {
    super(scope, id);

    const stack = cdk.Stack.of(this);

    this.hearingMemory = new agentcore.Memory(this, 'HearingMemory', {
      memoryName: 'store_manager_hearing_memory',
      description: 'Memory for store hearing agent',
      expirationDuration: cdk.Duration.days(365),
    });

    this.dailySummaryMemory = new agentcore.Memory(this, 'DailySummaryMemory', {
      memoryName: 'store_manager_daily_summary_memory',
      description: 'Memory for daily summary agent',
      expirationDuration: cdk.Duration.days(365),
    });

    const agentImage = new ContainerImageBuild(this, 'AgentImage', {
      directory: path.join(__dirname, '../../../backend/store-agent'),
      platform: Platform.LINUX_ARM64,
    });

    const agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromImageUri(
      agentImage.imageUri
    );

    this.runtime = new agentcore.Runtime(this, 'StoreAgentRuntime', {
      runtimeName: 'store_manager_agent',
      agentRuntimeArtifact: agentRuntimeArtifact,
      description: 'Store Manager Agent Runtime',
      environmentVariables: {
        HEARING_AGENTCORE_MEMORY_ID: this.hearingMemory.memoryId,
        DAILY_SUMMARY_AGENTCORE_MEMORY_ID: this.dailySummaryMemory.memoryId,
        REGION: stack.region,
        TABLE_BUCKET_ARN: props.dataResources.tableBucket.attrTableBucketArn,
        NAMESPACE: props.dataResources.namespace.namespace,
        ATHENA_OUTPUT_LOCATION: `s3://${props.dataResources.athenaResultsBucket.bucketName}/results/`,
        PROMPT_BUCKET_NAME: props.dataResources.promptBucket.bucketName,
        PROMPT_PREFIX: 'prompt/',
        LOG_LEVEL: 'INFO',
        BEDROCK_MODEL_ID: 'jp.anthropic.claude-haiku-4-5-20251001-v1:0',
        BEDROCK_REGION: stack.region,
      },
    });

    props.dataResources.promptBucket.grantRead(this.runtime);
    props.dataResources.athenaResultsBucket.grantReadWrite(this.runtime);

    agentImage.repository.grantPull(this.runtime);

    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: ['*'],
      })
    );

    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['s3tables:*'],
        resources: [
          props.dataResources.tableBucket.attrTableBucketArn,
          `${props.dataResources.tableBucket.attrTableBucketArn}/*`,
          `${props.dataResources.tableBucket.attrTableBucketArn}/table/*`,
        ],
      })
    );

    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'athena:GetQueryExecution',
          'athena:GetQueryResults',
          'athena:StartQueryExecution',
          'athena:StopQueryExecution',
        ],
        resources: [
          `arn:aws:athena:${stack.region}:${stack.account}:workgroup/primary`,
        ],
      })
    );

    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'glue:Get*',
          'glue:UpdateTable'
        ],
        resources: ['*'],
      })
    );

    this.runtime.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [          
          'lakeformation:Get*',
          'lakeformation:List*'
        ],
        resources: ['*'],
      })
    );

    this.hearingMemory.grantRead(this.runtime);
    this.hearingMemory.grantWrite(this.runtime);
    this.dailySummaryMemory.grantRead(this.runtime);
    this.dailySummaryMemory.grantWrite(this.runtime);

    const bucketName = props.dataResources.tableBucket.tableBucketName!;
    const catalogId = `${stack.account}:s3tablescatalog/${bucketName}`;

    const s3TablesPermissions = new lakeformation.CfnPermissions(this, 'S3TablesPermissionsRuntime', {
      permissions: ['SELECT', 'INSERT', 'DELETE', 'DESCRIBE'],
      permissionsWithGrantOption: [],
      dataLakePrincipal: {
        dataLakePrincipalIdentifier: this.runtime.role.roleArn,
      },
      resource: {
        tableResource: {
          catalogId: catalogId,
          databaseName: props.dataResources.namespace.namespace,
          tableWildcard: {},
        },
      },
    });
    s3TablesPermissions.addDependency(props.dataResources.namespace);

    new cdk.CfnOutput(this, 'RuntimeArn', {
      value: this.runtime.agentRuntimeArn,
      description: 'AgentCore Runtime ARN',
    });
  }
}
