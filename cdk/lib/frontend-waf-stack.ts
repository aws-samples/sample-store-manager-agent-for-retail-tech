import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { FrontendWaf } from './constructs/frontend-waf';

export interface FrontendWafStackProps extends cdk.StackProps {
  allowedIpV4AddressRanges: string[];
  allowedIpV6AddressRanges: string[];
}

export class FrontendWafStack extends cdk.Stack {
  public readonly webAclArn: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props: FrontendWafStackProps) {
    super(scope, id, props);

    const waf = new FrontendWaf(this, 'FrontendWaf', {
      allowedIpV4AddressRanges: props.allowedIpV4AddressRanges,
      allowedIpV6AddressRanges: props.allowedIpV6AddressRanges,
    });

    this.webAclArn = new cdk.CfnOutput(this, 'WebAclArn', {
      value: waf.webAcl.attrArn,
      exportName: `${this.stackName}-WebAclArn`,
    });
  }
}
