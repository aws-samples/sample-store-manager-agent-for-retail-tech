# テストガイド

このドキュメントでは、各種テスト実行方法について記載します。

## テスト概要

本サンプルでは以下のテストを提供しています：

- **ローカルテスト**: Docker環境でのAPIテスト
- **AWSテスト**: デプロイ済み環境での統合テスト
- **フロントエンドテスト**: Vitestによるコンポーネントテスト

### 環境セットアップ

#### バックエンドテスト環境

- **Python環境**: Python 3.13が必要
- **uv**: Pythonパッケージ管理ツール
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
-  **Docker**: docker コマンドを実行できる状態に環境をセットアップしてください。Docker Desktop を業務利用する場合は多くの場合 [サブスクリプション契約が必要](https://www.docker.com/legal/docker-subscription-service-agreement/) ですので、ご注意ください。
	- CDK デプロイ時はコンテナを AWS CodeBuild で build するため Docker なしでもアプリの利用は可能です。
	- Local 環境での API テストを docker 上で行うため、継続的な開発を行う際に必要になります。
- **AWS CLI**: AWSテスト用
- **AWS認証情報**: 適切に設定されたAWSクレデンシャル

#### フロントエンドテスト環境

- **Node.js**: バージョン18以上
- **npm**: パッケージ管理

## テスト詳細: テスト項目一覧

### バックエンド
#### Unit Test
#####  APIテスト
```bash
## テスト実行方法

bash
cd backend/agent-api

# テスト依存関係をインストール
uv sync --extra test

# 全テスト実行
uv run pytest tests/

# 単体テストのみ
uv run pytest tests/unit/

# Schemathesisテストのみ
uv run pytest tests/schema/
```

#####  AgentCore Runtime Local Unitテスト
会話履歴の管理先として、事前に AgentCore Memory の設定のみ事前に必要になります。

```bash
cd backend/test
uv run agentcore/local_test.py
```

**テスト内容**:
- ヒアリングエージェントの動作確認
- 日次サマリーエージェントの動作確認
- 会話履歴の管理
- ツール呼び出しの確認
#### Integration Test

#####  事前準備
- CDK スタックがデプロイ済み（`cdk/.cdk-outputs.json` が存在）
- AWS CLI 認証情報が設定済み（`~/.aws/credentials`）
#####  AgentCore Runtime テスト
AgentCore Runtime上のエージェントを直接テストします。

```bash
cd backend/test/agentcore
uv sync

# AWS環境テスト（AgentCore Runtime）
uv run runtime_test.py
```

**テスト内容**:
- ヒアリングエージェントの動作確認
- 日次サマリーエージェントの動作確認
- 会話履歴の管理
- ツール呼び出しの確認

#####  ローカル環境でのAPIテスト

Docker環境でローカルにAPIをデプロイしてテストします。

```bash
cd backend/test
uv sync
uv run test_local.py

# 特定モジュールのみ
uv run test_local.py --module admin 

# パラメータ確認
uv run test_local.py -h
usage: test_local.py [-h] [--module {admin,survey,chat,insights,admin_errors,survey_errors,insights_errors,agent}]
                     [--verbose]

Store Daily QA System Test Runner

options:
  -h, --help            show this help message and exit
  --module {admin,survey,chat,insights,admin_errors,survey_errors,insights_errors,agent}
                        Run tests for specific module only
  --verbose, -v         Enable verbose output
```

**テスト内容**:
- AgentCore Runtime 実行
- 基本的なAPI機能のテスト
- データベース操作（S3 Tables + Athena）のテスト
- エラーハンドリングのテスト

##### AWS環境でのAPI統合テスト

デプロイ済みのAWS環境に対してE2Eテストを実行します。

```bash
cd backend/test
uv sync

# 初回実行(Cognitoユーザー登録あり)
uv run test_aws.py --user メールアドレス --pass パスワード --first

# 2回目以降実行(既存Cognitoユーザー利用)
uv run test_aws.py --user メールアドレス --pass パスワード

# パラメータ確認
uv run test_aws.py -h
usage: test_aws.py [-h] [--module {admin,survey,chat,insights,admin_errors,survey_errors,insights_errors,agent}]
                   [--verbose] [--user USER] [--pass PASSWORD] [--first]

AWS API Gateway Test Runner

options:
  -h, --help            show this help message and exit
  --module {admin,survey,chat,insights,admin_errors,survey_errors,insights_errors,agent}
                        Run tests for specific module only
  --verbose, -v         Enable verbose output
  --user USER           Cognito user email address
  --pass PASSWORD       Cognito user password
  --first               First time execution - create Cognito user
```

**テスト内容**:
- Cognito 認証確認
- API Gateway + Lambda の実行確認
- AgentCore Runtime 実行
- 基本的なAPI機能のテスト
- データベース操作（S3 Tables + Athena）のテスト
- エラーハンドリングのテスト

### フロントエンドテスト

#### 1. コンポーネントテスト

Vitestを使用したReactコンポーネントのテストを実行します。

```bash
cd frontend
npm install
npm run test
```

**テスト内容**:
- ページコンポーネントのレンダリング
- フォームコンポーネントの動作
- ストア（状態管理）の動作
- APIクライアントの動作
- ユーティリティ関数の動作

#### 2. ローカル起動テスト

フロントエンドをローカルで起動して動作確認します。

```bash
cd frontend/test
./local_launch_app.sh
```

> [!NOTE]
> このスクリプトは以下を自動的に実行します：
> - CDK出力からAPI設定を取得
> - 環境変数ファイルの生成
> - Vite開発サーバーの起動

ブラウザで`http://localhost:5173`にアクセスして動作確認します。

#### 3. ビルドテスト

本番用ビルドをテストします。

```bash
cd frontend
npm run build
```

ブラウザで`http://localhost:4173`にアクセスして動作確認します。


### AWS環境でのエラー時のデバッグ

テスト失敗時は以下をコンソールや AWS CLI などで確認：

1. **CloudWatch Logs**: Lambda関数 / AgentCore Runtime の処理エラーを確認
2. **Athenaクエリ履歴**: クエリエラー/DB権限エラー確認
3. **CloudTrail**: IAM 権限周りでのエラー確認
4. **API Gatewayログ**:API Gateway 設定などによるエラー確認
5. **ブラウザコンソール**: フロントエンドエラーを確認

```bash
# Lambda関数のログを確認
aws logs tail /aws/lambda/StoreManager-ApiLambda --follow

# Athenaクエリ履歴を確認
aws athena list-query-executions --max-results 10
```
