# デプロイ手順

## 事前準備

### 環境セットアップ

デプロイには、以下の環境が必要です。事前に環境のセットアップを実施してください。

- **Node.js**: バージョン24以上が必要です
- **AWS CLI**: AWSリソースの管理に使用します
- **AWS CDK**: インフラストラクチャのプロビジョニングに使用します
  ```bash
  npm install -g aws-cdk
  ```
- **AWS認証情報の設定**: AWSの認証情報を`$HOME/.aws/config`に設定してください
-  **Docker**: docker コマンドを実行できる状態に環境をセットアップしてください。Docker Desktop を業務利用する場合は多くの場合 [サブスクリプション契約が必要](https://www.docker.com/legal/docker-subscription-service-agreement/) ですのでご注意ください。
	- CDK デプロイ時はコンテナを AWS CodeBuild で build するため Docker なしでもアプリの利用は可能です。
	- Local 環境での API テストを docker 上で行うため、継続的な開発を行う際に必要になります。
- **Python**: バージョン3.13が必要です（バックエンドAPI用）
- **uv**: Pythonパッケージ管理に使用します
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

> [!NOTE]
> デプロイ先のAWSアカウントとリージョンを事前に決定してください。デフォルトリージョンは`ap-northeast-1`です。

### AWS環境
- 該当リージョンで Bedrock モデルが利用できることを事前にコンソールなどから確認ください。（ 2025q4-store-manager-agent/cdk/lib/constructs/agentcore-resources.ts 内の agentcore runtime 環境変数設定から変更可能 ）
	- デフォルトリージョン: `ap-northeast-1`
	- デフォルトモデル: `jp.anthropic.claude-haiku-4-5-20251001-v1:0`
- API Gateway の [Timeout Quota （`Maximum integration timeout in milliseconds`）](https://ap-northeast-1.console.aws.amazon.com/servicequotas/home/services/apigateway/quotas/L-E5AE38E3)の緩和申請を実施ください
	- AWS のデフォルトのクォータ値: 29,000 ミリ秒
	- 緩和申請値: 90,000 ミリ秒
- S3 Tables AWS 分析サービスとの統合
![[img/s3-tables-setup.png]]
[S3 tables コンソール画面](https://ap-northeast-1.console.aws.amazon.com/s3/table-buckets?region=ap-northeast-1)から統合を有効化

## デプロイ手順

### 1. プロジェクトフォルダの展開

```bash
unzip 2025q4-store-manager-agent-main.zip
cd 2025q4-store-manager-agent-main/
```

### 2. CDK環境の準備

#### npm モジュールインストール
```bash
cd cdk
npm install
```

#### CDK Bootstrap
> [!IMPORTANT]
> 初回デプロイ時のみ、CDK Bootstrapが必要です。

 ```bash
 AWS_REGION=ap-northeast-1 npx cdk bootstrap
 AWS_REGION=us-east-1 npx cdk bootstrap
 ```


#### Lake Formation 設定
事前に以下の手順で Lake Formation での設定権限を、お客様環境で使用されている IAM ユーザーに紐づくIAM role と CDK bootstrap で自動作成される以下の IAM role に追加が必要です。

> [!NOTE]
> Lake Formation の権限モデルについて: Lake Formation は IAM とは独立した権限モデルを持っており、IAM の AdministratorAccess があっても、Lake Formation のデータレイク管理者として明示的に登録されていない限り、Lake Formation リソースへのアクセスは制限されます。

##### AWS CLI コマンド
```bash
aws lakeformation put-data-lake-settings \
  --region ap-northeast-1 \
  --data-lake-settings '{
	"DataLakeAdmins": [
	  {"DataLakePrincipalIdentifier": "arn:aws:iam::0000000:role/IAMユーザーに紐づくロール名"},
	  {"DataLakePrincipalIdentifier": "arn:aws:iam::0000000:role/cdk-XXXXXXXX-cfn-exec-role-0000000-ap-northeast-1"}
	]
  }'
```

##### AWS コンソールでの追加手順

1. Lake Formation コンソールを開く
   - https://console.aws.amazon.com/lakeformation/

2. Administrative roles and tasksに移動
   - 左側のナビゲーションメニューから「Administrative roles and tasks」をクリック

3. Data lake administrators セクション
   - 「Data lake administrators」セクションを見つける
   - 「Add」ボタンをクリック

4. 管理者を追加
   - 「IAM users and roles」を選択
   - ロール名を入力: cdk-XXXXXXXX-cfn-exec-role-0000000-ap-northeast-1
   - または ARN を入力: arn:aws:iam::0000000:role/cdk-XXXXXXXX-cfn-exec-role-0000000-ap-northeast-1
   - お客様環境で使用されている IAM ユーザーに紐づくIAM roleにも同様に追加
	   - arn:aws:iam::0000000:role/IAMユーザーに紐づくロール名
   - 「Save」をクリック

### 3. CDK設定のカスタマイズ

`cdk/cdk.json`で以下の設定をカスタマイズできます：

```json
{
  "context": {
    "selfSignUpEnabled": true,
    "allowedSignUpEmailDomains": ["example.com"],
    "autoJoinUserGroups": ["admin"],
    "allowedIpV4AddressRanges": ["0.0.0.0/1", "128.0.0.0/1"],
    "allowedIpV6AddressRanges": [
      "0000:0000:0000:0000:0000:0000:0000:0000/1",
      "8000:0000:0000:0000:0000:0000:0000:0000/1"
    ]
  }
}
```

> [!Note]
> - selfSignUpEnabled: アプリ画面でユーザー作成を許可
> - allowedSignUpEmailDomains: サインナップ可能メールアドレス
> - autoJoinUserGroups: 自動追加するUserGroup
> - allowedIpV4AddressRanges: IP制限設定
> - allowedIpV6AddressRanges: IP制限設定

### 4. CDKデプロイ

```bash
cd cdk
npx cdk deploy --all --require-approval never --outputs-file ./.cdk-outputs.json
```

> [!NOTE]
> デプロイには20分程度かかります。以下のリソースが作成されます：
> - S3（バケットストレージ）
> - S3 Tables（データストレージ）
> - Amazon Athena（データクエリ）
> - AgentCore Runtime（AIエージェント実行環境）
> - AgentCore Memory（会話履歴管理）
> - Lambda関数（API処理）
> - API Gateway（REST API）
> - Amazon Cognito（認証）
> - CloudFront（フロントエンド配信）

### 5. 初期データのセットアップ

デプロイ完了後、初期データをS3 Tablesに投入します。
```bash
cd ../data-import
uv sync
```
1. 設定ファイル作成
```bash
uv run generate_config.py
```

2. テストデータ解凍
	フォルダ・データ構造を参考にお客様データに変更してください
```bash
unzip test-data.zip
```

3. CSVデータ転送
```bash
uv run s3_transfer.py
```

3. テーブル作成
```bash
uv run create_s3_tables.py
```

4. テスト用前日survey+売上サンプルデータ追加
```bash
uv run insert_s3_tables_test_data.py
```

> [!IMPORTANT]
> この処理では以下のテーブルが作成され、初期データが投入されます：
> - `questions`: アンケート質問マスタ
> - `messages`: システムメッセージマスタ
> - `daily_survey_answers`: アンケート回答データ
> - `daily_survey_summary`: 日次サマリーデータ
> - `chat_history`: AI対話履歴

### 6. デプロイ確認

デプロイが成功したことを確認します。

```bash
# CDK出力の確認
cat cdk/.cdk-outputs.json
```

CloudFormationの出力から以下の情報を取得できます：
- `FrontendUrl`: フロントエンドアプリケーションのURL
- `ApiEndpoint`: REST APIのエンドポイント
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito User Pool Client ID

### 7. ユーザー作成

初回ログイン用のユーザーを作成します。

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <USER_POOL_ID> \
  --username <EMAIL> \
  --user-attributes Name=email,Value=<EMAIL> Name=email_verified,Value=true \
  --temporary-password <TEMP_PASSWORD>
```

> [!TIP]
> `selfSignUpEnabled: true`の場合、ユーザーはフロントエンドから自己登録できます。

## リソース削除

> [!CAUTION]
> リソース削除は不可逆的な操作です。すべてのデータが失われます。

### S3バケットの空にする

CDKスタック削除前に、S3バケットを空にする必要があります。

```bash
# データソースバケットを空にする
aws s3 rm s3://<DATA_SOURCE_BUCKET_NAME> --recursive

# Athena結果バケットを空にする
aws s3 rm s3://<ATHENA_RESULTS_BUCKET_NAME> --recursive

# フロントエンドバケットを空にする
aws s3 rm s3://<FRONTEND_BUCKET_NAME> --recursive
```

### CDKスタックの削除

```bash
# バックエンドスタックの削除
cd cdk
cdk destroy BackendStack

# WAFスタックの削除（us-east-1）
cdk destroy StoreManagerFrontendWafStack --region us-east-1

# 一括削除
cdk destroy --all
```

> [!WARNING]
> - S3 Tablesのデータを削除すると、すべてのアンケート回答、AI対話履歴、レポートが失われます。必要に応じて事前にバックアップを取得してください。


### 手動削除
以下のリソースについては `cdk destroy` で削除されないため、手動での削除が必要です
- S3 バケット
- Cognito User Pool