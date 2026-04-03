import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as lakeformation from 'aws-cdk-lib/aws-lakeformation';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import { Construct } from 'constructs';
import * as path from 'path';
import { ContainerImageBuild } from 'deploy-time-build';
import { DataResourcesConstruct } from './data-resources';
import { AgentCoreResourcesConstruct } from './agentcore-resources';
import { Auth } from './auth';
import { WebAclForApi } from './webacl-for-api';

export interface ApiLambdaProps {
  dataResources: DataResourcesConstruct;
  agentcoreResources: AgentCoreResourcesConstruct;
  auth: Auth;
  webAcl: WebAclForApi;
}

export class ApiLambdaConstruct extends Construct {
  public readonly api: apigateway.RestApi;
  public readonly apiFunction: lambda.DockerImageFunction;
  public readonly apiUrl: string;

  constructor(scope: Construct, id: string, props: ApiLambdaProps) {
    super(scope, id);

    const stack = cdk.Stack.of(this);
    const apiTimeout = cdk.Duration.seconds(90);

    const apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      logGroupName: '/aws/lambda/StoreManagerApiFunction',
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const apiImage = new ContainerImageBuild(this, 'ApiImage', {
      directory: path.join(__dirname, '../../../backend/agent-api'),
      platform: Platform.LINUX_AMD64,
    });

    this.apiFunction = new lambda.DockerImageFunction(this, 'ApiFunction', {
      code: apiImage.toLambdaDockerImageCode(),
      architecture: lambda.Architecture.X86_64,
      memorySize: 1024,
      timeout: apiTimeout,
      environment: {
        LOG_LEVEL: 'INFO',
        REGION: stack.region,
        TABLE_BUCKET_ARN: props.dataResources.tableBucket.attrTableBucketArn,
        NAMESPACE: props.dataResources.namespace.namespace,
        ATHENA_OUTPUT_LOCATION: `s3://${props.dataResources.athenaResultsBucket.bucketName}/results/`,
        ATHENA_WORKGROUP: 'primary',
        AGENTCORE_RUNTIME_ARN: props.agentcoreResources.runtime.agentRuntimeArn,
        AGENTCORE_REGION: stack.region,
        HEARING_AGENTCORE_MEMORY_ID: props.agentcoreResources.hearingMemory.memoryId,
        DAILY_SUMMARY_AGENTCORE_MEMORY_ID: props.agentcoreResources.dailySummaryMemory.memoryId,
        UV_CACHE_DIR: '/tmp/.uv-cache',
      },
      logGroup: apiLogGroup,
      description: 'Store Manager Agent API - FastAPI on Lambda',
    });

    props.dataResources.dataSourceBucket.grantReadWrite(this.apiFunction);
    props.dataResources.athenaResultsBucket.grantReadWrite(this.apiFunction);

    this.apiFunction.addToRolePolicy(
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

    this.apiFunction.addToRolePolicy(
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

    this.apiFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'glue:Get*',
          'glue:UpdateTable'
        ],
        resources: ['*'],
      })
    );

    this.apiFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'lakeformation:Get*',
          'lakeformation:List*'
        ],
        resources: ['*'],
      })
    );

    props.agentcoreResources.runtime.grantInvoke(this.apiFunction);
    props.agentcoreResources.hearingMemory.grantRead(this.apiFunction);
    props.agentcoreResources.hearingMemory.grantWrite(this.apiFunction);
    props.agentcoreResources.dailySummaryMemory.grantRead(this.apiFunction);
    props.agentcoreResources.dailySummaryMemory.grantWrite(this.apiFunction);

    const accessLogGroup = new logs.LogGroup(this, 'ApiAccessLogs', {
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.api = new apigateway.RestApi(this, 'Api', {
      restApiName: 'Store Manager Agent API',
      description: 'API for Store Manager Agent',
      endpointTypes: [apigateway.EndpointType.REGIONAL],
      deployOptions: {
        stageName: 'prod',
        metricsEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        accessLogDestination: new apigateway.LogGroupLogDestination(accessLogGroup),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields(),
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
      },
      cloudWatchRole: true,
    });

    const lambdaIntegration = new apigateway.LambdaIntegration(
      this.apiFunction,
      {
        timeout: apiTimeout,
      }
    );

    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'ApiAuthorizer', {
      cognitoUserPools: [props.auth.userPool],
      identitySource: 'method.request.header.Authorization',
    });

    this.api.root.addProxy({
      defaultIntegration: lambdaIntegration,
      anyMethod: true,
      defaultMethodOptions: {
        authorizationType: apigateway.AuthorizationType.COGNITO,
        authorizer: authorizer,
      },
    });

    this.apiUrl = this.api.url;

    const wafAssociation = new wafv2.CfnWebACLAssociation(this, 'ApiWafAssociation', {
      resourceArn: `arn:aws:apigateway:${stack.region}::/restapis/${this.api.restApiId}/stages/prod`,
      webAclArn: props.webAcl.webAcl.attrArn,
    });

    wafAssociation.node.addDependency(this.api.deploymentStage);

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.api.url,
      description: 'API Gateway URL',
    });

    new cdk.CfnOutput(this, 'ApiFunctionArn', {
      value: this.apiFunction.functionArn,
      description: 'Lambda Function ARN',
    });

    // S3 Tables ARN format: arn:aws:s3tables:region:account-id:bucket/bucket-name
    const tableBucketArn = props.dataResources.tableBucket.attrTableBucketArn;
    const accountId = cdk.Fn.select(4, cdk.Fn.split(':', tableBucketArn));
    const bucketResource = cdk.Fn.select(5, cdk.Fn.split(':', tableBucketArn)); // "bucket/bucket-name"
    const bucketName = cdk.Fn.select(1, cdk.Fn.split('/', bucketResource));
    const catalogId = `${accountId}:s3tablescatalog/${bucketName}`;

    const s3TablesPermissions = new lakeformation.CfnPermissions(this, 'S3TablesPermissions', {
      permissions: ['SELECT', 'INSERT', 'DELETE', 'DESCRIBE', 'ALTER'],
      permissionsWithGrantOption: [],
      dataLakePrincipal: {
        dataLakePrincipalIdentifier: this.apiFunction.role!.roleArn,
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
  }
}
