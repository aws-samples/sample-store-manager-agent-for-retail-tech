# AWS Glue Data Catalog テーブル設計書

## 概要

店舗スタッフの日次QAシステムの機能要件に基づくAWS Glue Data Catalogテーブル設計です。S3上のCSVファイルをベースとした設計で、日次回答機能、AI対話機能、日報生成機能、管理者機能をサポートします。

## テーブル設計

### 管理者データ
#### admin_survey
##### description
管理者が設定する定型質問を管理します。
##### table schema
| カラム名          | データ型          | 説明                                   |
| ------------- | ------------- | ------------------------------------ |
| id            | string        | UUID形式の一意識別子                         |
| question_text | string        | 質問内容                                 |
| question_type | string        | 質問タイプ (text, choice, rating, number) |
| options       | array<string> | 選択肢（choice型の場合）                      |
| is_active     | boolean       | アクティブ状態                              |
| created_by    | string        | 作成者のCognito sub                      |
| created_at    | timestamp     | 作成日時                                 |
| updated_at    | timestamp     | 更新日時                                 |

#### admin_messages
##### description
管理者が設定する本部から店舗への周知メッセージを管理します。
##### table schema
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| id | string | UUID形式の一意識別子 |
| title | string | メッセージタイトル |
| content | string | メッセージ内容 |
| is_active | boolean | アクティブ状態 |
| created_by | string | 作成者のCognito sub |
| created_at | timestamp | 作成日時 |
| updated_at | timestamp | 更新日時 |

### サーベイ結果
#### daily_survey_summary
##### description
日次レポートの基本情報とユーザー情報を管理するメインテーブルです。
##### table schema
| カラム名                | データ型      | 説明                                          |
| ------------------- | --------- | ------------------------------------------- |
| id                  | string    | UUID形式の一意識別子                                |
| user_cd             | string    | ユーザーコード=Cognito User Pool の sub             |
| str_cd              | string    | 店舗コード                                       |
| report_date         | timestamp | レポート対象日                                     |
| status              | string    | セッション状態 (in_progress, completed, cancelled) |
| report_text         | string    | レポートテキスト                                    |
| agentcore_memory_id | string    | AgentCore Memory リソースID                     |
| session_id          | string    | 会話セッションID                                   |
| actor_id            | string    | ユーザー/アクターID                                 |
| user_feedback       | string    | AIフィードバックに対するユーザーの感想                        |
| created_at          | timestamp | 作成日時                                        |
| updated_at          | timestamp | 更新日時                                        |
| supplement_comment  | string    | 補足コメント                                      |

#### daily_survey_answers
##### description
各質問に対する回答の詳細情報を管理するテーブルです。
##### table schema
| カラム名          | データ型      | 説明                             |
| ------------- | --------- | ------------------------------ |
| id            | string    | UUID形式の一意識別子                   |
| summary_id    | string    | 回答サマリテーブルのID                   |
| survey_id     | string    | 1surveyに複数の質問を紐付けるための、質問グループID |
| user_cd       | string    | ユーザーコード                        |
| str_cd        | string    | 店舗コード                          |
| question_text | string    | 質問内容                           |
| question_type | string    | 質問タイプ (rating, choice, text)   |
| answer_value  | string    | 回答値                            |
| options       | string    | 選択肢（choice型の場合）                |
| created_at    | timestamp | 作成日時                           |
| updated_at    | timestamp | 更新日時                           |

#### ai_chat_history
##### description
AIとのチャット履歴を管理するテーブルです。
##### table schema
| カラム名                | データ型      | 説明                          |
| ------------------- | --------- | --------------------------- |
| id                  | string    | UUID形式の一意識別子                |
| summary_id          | string    | 回答サマリテーブルのID                |
| survey_id           | string    | daily_survey_answersと紐付けるID |
| agentcore_memory_id | string    | AgentCore Memory リソースID     |
| session_id          | string    | 会話セッションID                   |
| actor_id            | string    | ユーザー/アクターID                 |
| created_at          | timestamp | 作成日時                        |

### 売上データ
#### t_sales
##### description
店舗の売上明細データを管理します。
##### table schema
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| terminal_no | string | ターミナル番号 |
| receipt_no | string | 伝票番号/レシート番号 |
| str_cd | string | 店舗コード |
| sales_date_time | timestamp | 伝票日時 |
| sku | string | SKU |
| br_cd | string | ブランドコード |
| item_cd | string | アイテムコード |
| is_sale | string | セールフラグ |
| sales_quantity | bigint | 売上数量 |
| sales_cost | double | 売上原価 |
| sales_amount | double | 売上金額 |
| customer_count | bigint | 買上客数 |

#### t_str_daily_budget
##### description
店舗の日次予算データを管理します。
##### table schema
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| str_cd | string | 店舗コード |
| date | timestamp | 年月日 |
| br_cd | string | ブランドコード |
| sales_budget | double | 予算金額 |

#### t_daily_store_traffic
##### description
店舗の来店客数と天気情報を管理します。
##### table schema
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| str_cd | string | 店舗コード |
| date | timestamp | 年月日 |
| weather_code | int | 天気コード |
| low_temp | string | 最低気温 |
| high_temp | string | 最高気温 |
| visitor_count | decimal | 入店客数 |

#### m_item
##### description
商品アイテムのマスタ情報を管理します。
##### table schema
| カラム名 | データ型 | 説明 |
|---------|---------|------|
| sku | string | SKU |
| product_code | string | 品番/商品コード |
| product_name | string | 品番名/商品名 |
| br_cd | string | ブランドコード |
| br_name | string | ブランド名 |
| item_cd | string | アイテムコード |
| item_name | string | アイテム名 |


## データ型の注意事項

AWS Glue Data Catalogでは以下のデータ型を使用します：

- `string`: 文字列
- `int`: 整数
- `bigint`: 大きな整数
- `double`: 浮動小数点数
- `decimal(p,s)`: 固定小数点数
- `boolean`: 真偽値
- `date`: 日付
- `timestamp`: タイムスタンプ
- `array<type>`: 配列
- `struct<field:type>`: 構造体

JSON形式のデータは`string`型として保存し、アプリケーション側でパースします。
