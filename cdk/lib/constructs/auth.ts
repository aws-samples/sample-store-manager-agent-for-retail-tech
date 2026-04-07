import * as cdk from 'aws-cdk-lib';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { IdentityPool, UserPoolAuthenticationProvider } from 'aws-cdk-lib/aws-cognito-identitypool';
import { Construct } from 'constructs';
import * as path from 'path';

export interface AuthProps {
  selfSignUpEnabled: boolean;
  allowedSignUpEmailDomains: string[];
  autoJoinUserGroups: string[];
}

export class Auth extends Construct {
  public readonly userPool: cognito.UserPool;
  public readonly userPoolClient: cognito.UserPoolClient;
  public readonly identityPool: IdentityPool;

  constructor(scope: Construct, id: string, props: AuthProps) {
    super(scope, id);

    const { selfSignUpEnabled, allowedSignUpEmailDomains, autoJoinUserGroups } = props;

    this.userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: `${cdk.Stack.of(this).stackName}-user-pool`,
      selfSignUpEnabled: selfSignUpEnabled,
      signInAliases: {
        email: true,
        username: false,
      },
      autoVerify: {
        email: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    if (allowedSignUpEmailDomains.length > 0) {
      const preSignUpFunction = new lambda.Function(this, 'PreSignUpFunction', {
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: 'app.handler',
        code: lambda.Code.fromAsset(
          path.join(__dirname, '../../lambda/cognito_triggers/pre_sign_up')
        ),
        environment: {
          ALLOWED_SIGN_UP_EMAIL_DOMAINS_STR: JSON.stringify(allowedSignUpEmailDomains),
        },
      });

      this.userPool.addTrigger(
        cognito.UserPoolOperation.PRE_SIGN_UP,
        preSignUpFunction
      );
    }

    if (autoJoinUserGroups.length > 0) {
      autoJoinUserGroups.forEach(groupName => {
        new cognito.CfnUserPoolGroup(this, `UserPoolGroup-${groupName}`, {
          userPoolId: this.userPool.userPoolId,
          groupName: groupName,
          description: `Auto-created group: ${groupName}`,
        });
      });

      const postConfirmationFunction = new lambda.Function(this, 'PostConfirmationFunction', {
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: 'app.handler',
        code: lambda.Code.fromAsset(
          path.join(__dirname, '../../lambda/cognito_triggers/post_confirmation')
        ),
        environment: {
          USER_POOL_ID: this.userPool.userPoolId,
          AUTO_JOIN_USER_GROUPS_STR: JSON.stringify(autoJoinUserGroups),
        },
      });

      postConfirmationFunction.addToRolePolicy(
        new cdk.aws_iam.PolicyStatement({
          effect: cdk.aws_iam.Effect.ALLOW,
          actions: ['cognito-idp:AdminAddUserToGroup'],
          resources: [this.userPool.userPoolArn],
        })
      );
    }

    this.userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool: this.userPool,
      userPoolClientName: `${cdk.Stack.of(this).stackName}-client`,
      authFlows: {
        userPassword: true,
        userSrp: true,
        adminUserPassword: true,
      },
      generateSecret: false,
    });

    // Identity Pool（音声入力機能用 - Transcribe Streaming）
    this.identityPool = new IdentityPool(this, 'IdentityPool', {
      identityPoolName: `${cdk.Stack.of(this).stackName}-identity-pool`,
      authenticationProviders: {
        userPools: [new UserPoolAuthenticationProvider({ 
          userPool: this.userPool,
          userPoolClient: this.userPoolClient,
        })],
      },
      allowUnauthenticatedIdentities: false,
    });

    // 認証済みユーザーにTranscribe Streaming権限を付与
    this.identityPool.authenticatedRole.addToPrincipalPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'transcribe:StartStreamTranscription',
          'transcribe:StartStreamTranscriptionWebSocket',
        ],
        resources: ['*'],
      })
    );
  }
}
