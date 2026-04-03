import * as cdk from 'aws-cdk-lib';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import { Construct } from 'constructs';

export interface WebAclForApiProps {
  allowedIpV4AddressRanges: string[];
  allowedIpV6AddressRanges: string[];
}

export class WebAclForApi extends Construct {
  public readonly webAcl: wafv2.CfnWebACL;

  constructor(scope: Construct, id: string, props: WebAclForApiProps) {
    super(scope, id);

    const ipV4Set = new wafv2.CfnIPSet(this, 'AllowedIPv4Set', {
      name: `${cdk.Stack.of(this).stackName}-allowed-ipv4`,
      scope: 'REGIONAL',
      ipAddressVersion: 'IPV4',
      addresses: props.allowedIpV4AddressRanges,
    });

    const ipV6Set = new wafv2.CfnIPSet(this, 'AllowedIPv6Set', {
      name: `${cdk.Stack.of(this).stackName}-allowed-ipv6`,
      scope: 'REGIONAL',
      ipAddressVersion: 'IPV6',
      addresses: props.allowedIpV6AddressRanges,
    });

    this.webAcl = new wafv2.CfnWebACL(this, 'WebAcl', {
      name: `${cdk.Stack.of(this).stackName}-api-waf`,
      scope: 'REGIONAL',
      defaultAction: { block: {} },
      rules: [
        {
          name: 'AllowedIPv4Rule',
          priority: 1,
          statement: {
            ipSetReferenceStatement: {
              arn: ipV4Set.attrArn,
            },
          },
          action: { allow: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AllowedIPv4Rule',
          },
        },
        {
          name: 'AllowedIPv6Rule',
          priority: 2,
          statement: {
            ipSetReferenceStatement: {
              arn: ipV6Set.attrArn,
            },
          },
          action: { allow: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AllowedIPv6Rule',
          },
        },
        {
          name: 'AWSManagedRulesCommonRuleSet',
          priority: 10,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesCommonRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWSManagedRulesCommonRuleSet',
          },
        },
        {
          name: 'AWSManagedRulesKnownBadInputsRuleSet',
          priority: 11,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesKnownBadInputsRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWSManagedRulesKnownBadInputsRuleSet',
          },
        },
      ],
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: `${cdk.Stack.of(this).stackName}-api-waf`,
      },
    });
  }
}
