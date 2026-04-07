# Store Manager Agent for Retail Tech (SMART)

本プロジェクトは、店舗スタッフの日次業務を支援するAIエージェントシステムです。Amazon Bedrock AgentCoreを活用し、日次アンケート収集、AI分析、レポート生成を行い、店舗運営の改善をサポートします。

## 主要機能

- **日次アンケート管理**: 店舗スタッフからの日次フィードバック収集
- **AI対話エージェント**: Strands Agentsを使用した自然な対話によるヒアリング
- **自動レポート生成**: Amazon Bedrockによる日次サマリーと改善提案の自動生成
- **履歴管理**: 過去のアンケート結果とレポートの閲覧・検索
- **管理機能**: 質問項目とメッセージのカスタマイズ
- **音声入力**: Amazon Transcribe Streamingによるリアルタイム文字起こし

## AWSアーキテクチャ概要

![AWSアーキテクチャ概要](doc/img/architecture.png)

### 処理詳細

1. **ユーザー認証**: Amazon Cognito による認証・認可
2. **アンケート回答**: フロントエンドからの日次アンケート送信
3. **AI対話**: AgentCore Runtime上のStrands Agentsによる対話型ヒアリング
4. **データ保存**: S3 TablesへのIceberg形式でのデータ保存
5. **レポート生成**: Amazon Bedrockを使用した日次サマリー生成
6. **データ分析**: Amazon Athenaによるデータクエリと分析

### 主要コンポーネント

####  フロントエンド
- **S3**: フロントエンドアセットの配信
- **CloudFront**: グローバルCDN配信
- **WAF**: アクセス制御

#### バックエンド
- **API Gateway**: REST APIエンドポイント
- **WAF**: API保護とアクセス制御
- **Lambda**: API処理とビジネスロジック実行
- **AgentCore Runtime**: Strands Agentsの実行環境
- **AgentCore Memory**: エージェントの会話履歴管理

#### データベース
- **S3 Tables**: Iceberg形式のテーブルストレージ。主に以下を管理
  - アンケート回答データ
  - 日次インサイトデータ
  - AI対話履歴
  - 売上情報など
- **Amazon Athena**: SQLベースのデータクエリエンジン

## ドキュメント一覧

- [デプロイ方法](doc/DEPLOYMENT.md) - システムのデプロイ手順
- [開発ガイド](doc/DEVELOPMENT.md) - アーキテクチャ詳細と開発情報
- [テストガイド](doc/TEST.md) - テスト実行方法

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.