# 音声入力機能 実装記録

## 概要
テキストボックスに音声入力機能を追加。Amazon Transcribe Streamingを使用したリアルタイム文字起こし。

## 実装ステップ

### Step 1: CDK - Identity Pool追加 ✅ 完了

**目的**: Transcribe Streamingを呼び出すためのAWS認証情報をフロントエンドに提供

**修正ファイル**:

#### 1. `cdk/lib/constructs/auth.ts`

**追加したimport**:
```typescript
import * as iam from 'aws-cdk-lib/aws-iam';
import { IdentityPool, UserPoolAuthenticationProvider } from 'aws-cdk-lib/aws-cognito-identitypool';
```

**追加したプロパティ**:
```typescript
public readonly identityPool: IdentityPool;
```

**追加したコード（UserPoolClient作成後）**:
```typescript
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
```

#### 2. `cdk/lib/backend-stack.ts`

**追加したOutput**:
```typescript
new cdk.CfnOutput(this, 'IdentityPoolId', {
  value: auth.identityPool.identityPoolId,
  description: 'Cognito Identity Pool ID (for Transcribe Streaming)',
  exportName: 'StoreManager-IdentityPoolId',
});
```

**デプロイ結果**:
- Identity Pool ID: `<your-identity-pool-id>`

---

### Step 2: フロントエンド - 環境変数追加 ✅ 完了

**修正ファイル**:

#### 1. `frontend/src/contexts/AuthContext.tsx`

**変更箇所**: Amplify.configure内にidentityPoolId追加
```typescript
Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: import.meta.env.VITE_APP_USER_POOL_ID,
      userPoolClientId: import.meta.env.VITE_APP_USER_POOL_CLIENT_ID,
      identityPoolId: import.meta.env.VITE_APP_IDENTITY_POOL_ID,  // 追加
    },
  },
});
```

#### 2. `cdk/lib/constructs/frontend.ts`

**変更箇所**: buildEnvPropsにVITE_APP_IDENTITY_POOL_ID追加
```typescript
const buildEnvProps = {
  VITE_API_BASE_URL: apiEndpoint,
  VITE_APP_REGION: region,
  VITE_APP_USER_POOL_ID: auth.userPool.userPoolId,
  VITE_APP_USER_POOL_CLIENT_ID: auth.userPoolClient.userPoolClientId,
  VITE_APP_IDENTITY_POOL_ID: auth.identityPool.identityPoolId,  // 追加
  VITE_APP_SELF_SIGN_UP_ENABLED: selfSignUpEnabled.toString(),
};
```

**テスト結果**:
- デプロイ成功
- FrontendBuildEnvVarsに`VITE_APP_IDENTITY_POOL_ID`が含まれていることを確認
- 既存機能（ログイン等）に影響なし

---

### Step 3: useVoiceInputフック作成 ✅ 完了（AudioWorklet版）

**作成ファイル**:
- `frontend/src/hooks/useVoiceInput.ts` - メインフック
- `frontend/public/worklets/recording-processor.js` - AudioWorkletプロセッサ

**追加した依存関係**:
```bash
npm install @aws-sdk/client-transcribe-streaming
```

**技術選定**:
- ❌ ScriptProcessorNode（非推奨、MDNで deprecated）
- ❌ microphone-stream（GenUで使用、内部でScriptProcessorNode使用）
- ✅ AudioWorklet（AWS公式推奨、ベストプラクティス）

**参考資料**:
- AWS公式ブログ: https://aws.amazon.com/blogs/machine-learning/stream-multi-channel-audio-to-amazon-transcribe-using-the-web-audio-api/
- MDN AudioWorklet: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet

**AudioWorkletの仕組み**:
1. `recording-processor.js`が別スレッドで音声処理
2. `process()`メソッドで128サンプルずつ受信
3. バッファに蓄積し、4096サンプルごとにPCMエンコードして送信
4. `port.postMessage()`でメインスレッドに送信
5. メインスレッドでTranscribe Streamingに送信

**フックの機能**:
- `startRecording()`: 録音開始、Transcribe Streaming接続
- `stopRecording()`: 録音停止、最終テキスト返却
- `cancelRecording()`: 録音キャンセル
- `state`: 'idle' | 'recording' | 'processing' | 'error'
- `isRecording`: 録音中かどうか
- `duration`: 録音時間（ミリ秒）
- `error`: エラーメッセージ

**使用例**:
```typescript
const { 
  isRecording, 
  startRecording, 
  stopRecording, 
  error 
} = useVoiceInput({
  onFinalResult: (text) => setValue(prev => prev + text),
  onInterimResult: (text) => setInterim(text), // リアルタイム表示用
  onError: (err) => console.error(err),
});
```

**テスト結果**:
- TypeScriptビルド成功（`npx tsc --noEmit`）
- 非推奨警告なし（ScriptProcessorNode未使用）
- 依存関係インストール成功
- AudioWorklet構文チェック成功（`node --check`）
- Viteビルド成功（`npm run build`）
- workletファイルがdist/worklets/に正しく配置されることを確認

---

### Step 4: DailyAnswerPage - マイクボタン追加 ✅ 完了

**修正ファイル**:
- `frontend/src/components/forms/TextQuestion.tsx`

**変更内容**:
- `useVoiceInput`フックをインポート
- マイクボタン（IconButton）を追加
- 録音中はテキストフィールドの背景色を変更
- 中間結果（interimText）をリアルタイム表示
- 最終結果は既存テキストに追加

**UI仕様**:
- マイクアイコン: テキストフィールド右下に配置
- 録音中: 赤いマイクオフアイコン、背景が薄赤
- 停止中: 青いマイクアイコン
- 処理中: CircularProgress表示

**新しいprops**:
- `enableVoiceInput?: boolean` - 音声入力の有効/無効（デフォルト: true）

**テスト結果**:
- TypeScriptビルド成功
- Viteビルド成功
- デプロイ成功

**動作確認URL**: <your-cloudfront-url>

---

## 技術仕様

### 使用サービス
- Amazon Transcribe Streaming
- Amazon Cognito Identity Pool（認証済みユーザーのみ）

### IAM権限
```json
{
  "Effect": "Allow",
  "Action": [
    "transcribe:StartStreamTranscription",
    "transcribe:StartStreamTranscriptionWebSocket"
  ],
  "Resource": "*"
}
```

### 言語設定
- `ja-JP`（日本語）

---

## 参考資料
- 既存実装: `daily-report/src/voice-input/`
- AWS CDK Identity Pool: https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_cognito_identitypool-readme.html
- Transcribe Streaming IAM: https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazontranscribe.html


---

### Step 5: 残り画面への展開 ✅ 完了

**作成ファイル**:
- `frontend/src/components/common/VoiceTextField.tsx` - 共通コンポーネント

**修正ファイル**:
- `frontend/src/pages/AIChatPage.tsx` - チャット入力欄
- `frontend/src/pages/AnswerConfirmPage.tsx` - 補足コメントボックス

**VoiceTextFieldコンポーネント**:
MUIのTextFieldをラップし、マイクボタンを追加した共通コンポーネント。
- `value`: string - 現在の値
- `onChange`: (value: string) => void - 値変更コールバック
- `enableVoiceInput?: boolean` - 音声入力の有効/無効（デフォルト: true）
- その他のTextFieldPropsをそのまま渡せる

**テスト結果**:
- TypeScriptビルド成功
- Viteビルド成功
- デプロイ成功

**動作確認URL**: <your-cloudfront-url>

**追加修正**:
- VoiceTextFieldで外部から`value`がクリアされた時、内部状態もリセットするように修正（AIChatPageの送信後クリア対応）

---

## 完了サマリー

**実装した機能**:
- 3画面（DailyAnswerPage、AIChatPage、AnswerConfirmPage）のテキスト入力欄に音声入力ボタンを追加
- Amazon Transcribe Streamingによるリアルタイム文字起こし
- AudioWorklet使用（ベストプラクティス準拠）

**作成・修正ファイル一覧**:
| ファイル | 内容 |
|---------|------|
| `cdk/lib/constructs/auth.ts` | Identity Pool追加 |
| `cdk/lib/backend-stack.ts` | IdentityPoolId Output追加 |
| `cdk/lib/constructs/frontend.ts` | VITE_APP_IDENTITY_POOL_ID追加 |
| `frontend/package.json` | AWS SDK依存パッケージ追加 |
| `frontend/package-lock.json` | 依存パッケージのバージョン固定 |
| `frontend/src/contexts/AuthContext.tsx` | identityPoolId設定追加 |
| `frontend/public/worklets/recording-processor.js` | AudioWorkletプロセッサ |
| `frontend/src/hooks/useVoiceInput.ts` | 音声入力フック |
| `frontend/src/components/forms/TextQuestion.tsx` | マイクボタン追加 |
| `frontend/src/components/common/VoiceTextField.tsx` | 共通コンポーネント |
| `frontend/src/pages/AIChatPage.tsx` | VoiceTextField使用 |
| `frontend/src/pages/AnswerConfirmPage.tsx` | VoiceTextField使用 |
