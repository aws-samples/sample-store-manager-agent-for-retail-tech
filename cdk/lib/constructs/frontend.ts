import { Construct } from "constructs";
import { CfnOutput, Duration, RemovalPolicy, Stack } from "aws-cdk-lib";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as iam from "aws-cdk-lib/aws-iam";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
} from "aws-cdk-lib/aws-s3";
import {
  CachePolicy,
  Distribution,
  GeoRestriction,
  SecurityPolicyProtocol,
  ViewerProtocolPolicy,
} from "aws-cdk-lib/aws-cloudfront";
import { S3BucketOrigin } from "aws-cdk-lib/aws-cloudfront-origins";
import { NodejsBuild } from "deploy-time-build";
import * as path from 'path';

export interface FrontendProps {
  readonly apiEndpoint: string;
  readonly auth: any;
  readonly webAclId?: string;
}

export class Frontend extends Construct {
  readonly cloudFrontWebDistribution: Distribution;
  readonly assetBucket: Bucket;

  constructor(scope: Construct, id: string, props: FrontendProps) {
    super(scope, id);

    this.assetBucket = new Bucket(this, "AssetBucket", {
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      enforceSSL: true,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    this.cloudFrontWebDistribution = new Distribution(this, "Distribution", {
      defaultRootObject: "index.html",
      defaultBehavior: {
        origin: S3BucketOrigin.withOriginAccessControl(this.assetBucket),
        viewerProtocolPolicy: ViewerProtocolPolicy.HTTPS_ONLY,
        cachePolicy: CachePolicy.CACHING_OPTIMIZED,
      },
      minimumProtocolVersion: SecurityPolicyProtocol.TLS_V1_2_2021,
      geoRestriction: GeoRestriction.allowlist('JP'),
      webAclId: props.webAclId,
      errorResponses: [
        {
          httpStatus: 404,
          ttl: Duration.seconds(0),
          responseHttpStatus: 200,
          responsePagePath: "/",
        },
        {
          httpStatus: 403,
          ttl: Duration.seconds(0),
          responseHttpStatus: 200,
          responsePagePath: "/",
        },
      ],
    });

    this.buildAndDeploy(props.apiEndpoint, props.auth);

    new CfnOutput(this, 'AssetBucketName', {
      value: this.assetBucket.bucketName,
      description: 'S3 bucket name for frontend assets',
    });

    new CfnOutput(this, 'CloudFrontDistributionId', {
      value: this.cloudFrontWebDistribution.distributionId,
      description: 'CloudFront distribution ID',
    });

    new CfnOutput(this, 'CloudFrontDomainName', {
      value: this.cloudFrontWebDistribution.distributionDomainName,
      description: 'CloudFront distribution domain name',
    });

    new CfnOutput(this, 'FrontendUrl', {
      value: `https://${this.cloudFrontWebDistribution.distributionDomainName}`,
      description: 'Frontend URL',
    });
  }

  private buildAndDeploy(apiEndpoint: string, auth: any) {
    const region = Stack.of(this).region;
    const selfSignUpEnabled = this.node.tryGetContext('selfSignUpEnabled') ?? true;
    
    const buildEnvProps = {
      VITE_API_BASE_URL: apiEndpoint,
      VITE_APP_REGION: region,
      VITE_APP_USER_POOL_ID: auth.userPool.userPoolId,
      VITE_APP_USER_POOL_CLIENT_ID: auth.userPoolClient.userPoolClientId,
      VITE_APP_SELF_SIGN_UP_ENABLED: selfSignUpEnabled.toString(),
    };

    const reactBuild = new NodejsBuild(this, "ReactBuild", {
      nodejsVersion: 24,
      assets: [
        {
          path: path.join(__dirname, "../../../frontend/"),
          exclude: [
            "node_modules",
            "dist",
            "dev-dist",
            ".env",
            ".env.local",
          ],
          commands: ["npm ci"],
        },
      ],
      buildCommands: ["npm run build"],
      buildEnvironment: buildEnvProps,
      destinationBucket: this.assetBucket,
      distribution: this.cloudFrontWebDistribution,
      outputSourceDirectory: "dist",
    });

    const bucketDeploy = reactBuild.node
      .findAll()
      .find(
        (c) => c instanceof s3deploy.BucketDeployment
      ) as s3deploy.BucketDeployment;

    bucketDeploy?.handlerRole?.addToPrincipalPolicy(
      new iam.PolicyStatement({
        actions: [
          "cloudfront:CreateInvalidation",
          "cloudfront:GetInvalidation",
        ],
        resources: [
          `arn:aws:cloudfront::${Stack.of(this).account}:distribution/${
            this.cloudFrontWebDistribution.distributionId
          }`,
        ],
      })
    );

    new CfnOutput(this, 'FrontendBuildEnvVars', {
      value: JSON.stringify(buildEnvProps, null, 2),
      description: 'Environment variables for frontend build',
    });
  }
}
