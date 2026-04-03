#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { BackendStack } from '../lib/backend-stack';
import { FrontendWafStack } from '../lib/frontend-waf-stack';

const app = new cdk.App();

const wafStack = new FrontendWafStack(app, 'StoreManagerFrontendWafStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: 'us-east-1',
  },
  crossRegionReferences: true,
  allowedIpV4AddressRanges: app.node.tryGetContext('allowedIpV4AddressRanges') || [],
  allowedIpV6AddressRanges: app.node.tryGetContext('allowedIpV6AddressRanges') || []
});

new BackendStack(app, 'BackendStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'ap-northeast-1',
  },
  crossRegionReferences: true,
  description: 'Store Manager Agent API - FastAPI on Lambda with API Gateway',
  frontendWebAclArn: wafStack.webAclArn.value,
});

app.synth();

