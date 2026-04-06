import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { DataResourcesConstruct } from './constructs/data-resources';
import { AgentCoreResourcesConstruct } from './constructs/agentcore-resources';
import { ApiLambdaConstruct } from './constructs/api-lambda';
import { Frontend } from './constructs/frontend';
import { Auth } from './constructs/auth';
import { WebAclForApi } from './constructs/webacl-for-api';

export interface BackendStackProps extends cdk.StackProps {
  frontendWebAclArn?: string;
}

export class BackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: BackendStackProps) {
    super(scope, id, props);

    const selfSignUpEnabled = this.node.tryGetContext('selfSignUpEnabled') ?? true;
    const allowedSignUpEmailDomains = this.node.tryGetContext('allowedSignUpEmailDomains') ?? [];
    const autoJoinUserGroups = this.node.tryGetContext('autoJoinUserGroups') ?? [];
    const allowedIpV4AddressRanges = this.node.tryGetContext('allowedIpV4AddressRanges') ?? ['0.0.0.0/1', '128.0.0.0/1'];
    const allowedIpV6AddressRanges = this.node.tryGetContext('allowedIpV6AddressRanges') ?? [
      '0000:0000:0000:0000:0000:0000:0000:0000/1',
      '8000:0000:0000:0000:0000:0000:0000:0000/1'
    ];

    const auth = new Auth(this, 'Auth', {
      selfSignUpEnabled,
      allowedSignUpEmailDomains,
      autoJoinUserGroups,
    });

    const webAcl = new WebAclForApi(this, 'WebAcl', {
      allowedIpV4AddressRanges,
      allowedIpV6AddressRanges,
    });

    const dataResources = new DataResourcesConstruct(this, 'DataResources');

    const agentcoreResources = new AgentCoreResourcesConstruct(this, 'AgentCoreResources', {
      dataResources,
    });

    const apiLambda = new ApiLambdaConstruct(this, 'ApiLambda', {
      dataResources,
      agentcoreResources,
      auth,
      webAcl,
    });

    new Frontend(this, 'Frontend', {
      apiEndpoint: apiLambda.apiUrl,
      auth: auth,
      webAclId: props?.frontendWebAclArn,
    });

    new cdk.CfnOutput(this, 'DataSourceBucketName', {
      value: dataResources.dataSourceBucket.bucketName,
      description: 'S3 Bucket for CSV data source',
      exportName: 'StoreManager-DataSourceBucket',
    });

    new cdk.CfnOutput(this, 'DataSourceBucketArn', {
      value: dataResources.dataSourceBucket.bucketArn,
      description: 'S3 Bucket ARN for CSV data source',
      exportName: 'StoreManager-DataSourceBucketArn',
    });

    new cdk.CfnOutput(this, 'TableBucketArn', {
      value: dataResources.tableBucket.attrTableBucketArn,
      description: 'S3 Tables Bucket ARN',
      exportName: 'StoreManager-TableBucketArn',
    });

    new cdk.CfnOutput(this, 'NamespaceName', {
      value: dataResources.namespace.namespace,
      description: 'S3 Tables Namespace',
      exportName: 'StoreManager-Namespace',
    });

    new cdk.CfnOutput(this, 'AthenaWorkgroup', {
      value: 'primary',
      description: 'Athena Workgroup',
      exportName: 'StoreManager-AthenaWorkgroup',
    });

    new cdk.CfnOutput(this, 'AthenaOutputLocation', {
      value: `s3://${dataResources.athenaResultsBucket.bucketName}/results/`,
      description: 'Athena Query Results Location',
      exportName: 'StoreManager-AthenaOutputLocation',
    });

    new cdk.CfnOutput(this, 'AgentCoreRuntimeArn', {
      value: agentcoreResources.runtime.agentRuntimeArn,
      description: 'AgentCore Runtime ARN',
      exportName: 'StoreManager-AgentCoreRuntimeArn',
    });

    new cdk.CfnOutput(this, 'HearingMemoryId', {
      value: agentcoreResources.hearingMemory.memoryId,
      description: 'Hearing Memory ID',
      exportName: 'StoreManager-HearingMemoryId',
    });

    new cdk.CfnOutput(this, 'DailySummaryMemoryId', {
      value: agentcoreResources.dailySummaryMemory.memoryId,
      description: 'Daily Summary Memory ID',
      exportName: 'StoreManager-DailySummaryMemoryId',
    });

    new cdk.CfnOutput(this, 'PromptBucketName', {
      value: dataResources.promptBucket.bucketName,
      description: 'S3 Bucket for Agent Prompts',
      exportName: 'StoreManager-PromptBucket',
    });

    new cdk.CfnOutput(this, 'UserPoolId', {
      value: auth.userPool.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: 'StoreManager-UserPoolId',
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: auth.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
      exportName: 'StoreManager-UserPoolClientId',
    });

    new cdk.CfnOutput(this, 'IdentityPoolId', {
      value: auth.identityPool.identityPoolId,
      description: 'Cognito Identity Pool ID (for Transcribe Streaming)',
      exportName: 'StoreManager-IdentityPoolId',
    });

    new cdk.CfnOutput(this, 'WebAclArn', {
      value: webAcl.webAcl.attrArn,
      description: 'WAF Web ACL ARN',
      exportName: 'StoreManager-WebAclArn',
    });
  }
}
