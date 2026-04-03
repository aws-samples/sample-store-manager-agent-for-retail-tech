#!/bin/bash

# デプロイ済みのAPIを使用してローカルでReact Viteアプリを起動するスクリプト

# 色付き出力用の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ローカル環境でReact Viteアプリを起動 ===${NC}"

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# プロジェクトのルートディレクトリに移動
cd "${SCRIPT_DIR}/../.."
PROJECT_ROOT="$(pwd)"
echo -e "${YELLOW}プロジェクトルート: ${PROJECT_ROOT}${NC}"

# CDK出力ファイルのパス
CDK_OUTPUTS_FILE="${PROJECT_ROOT}/cdk/.cdk-outputs.json"

# CDK出力ファイルが存在するか確認
if [ ! -f "${CDK_OUTPUTS_FILE}" ]; then
    echo -e "${RED}エラー: CDK出力ファイルが見つかりません: ${CDK_OUTPUTS_FILE}${NC}"
    echo -e "${YELLOW}先に 'cdk deploy' を実行して出力ファイルを生成してください。${NC}"
    exit 1
fi

# jqがインストールされているか確認
if ! command -v jq &> /dev/null; then
    echo -e "${RED}エラー: jqが必要ですがインストールされていません。${NC}"
    echo -e "${YELLOW}jqをインストールしてください: brew install jq (macOSの場合)${NC}"
    exit 1
fi

# CDK出力からパラメータを抽出
echo -e "${YELLOW}CDK出力からパラメータを読み込んでいます...${NC}"

# フロントエンド用環境変数（JSON形式）を抽出
FRONTEND_ENV_VARS=$(jq -r '.BackendStack.FrontendFrontendBuildEnvVarsC8E75767' "${CDK_OUTPUTS_FILE}")

# フロントエンド環境変数から個別の値を抽出
API_BASE_URL=$(echo "${FRONTEND_ENV_VARS}" | jq -r '.VITE_API_BASE_URL')
USER_POOL_ID=$(echo "${FRONTEND_ENV_VARS}" | jq -r '.VITE_APP_USER_POOL_ID')
USER_POOL_CLIENT_ID=$(echo "${FRONTEND_ENV_VARS}" | jq -r '.VITE_APP_USER_POOL_CLIENT_ID')
REGION=$(echo "${FRONTEND_ENV_VARS}" | jq -r '.VITE_APP_REGION')

# 抽出したパラメータを検証
if [ "${API_BASE_URL}" = "null" ] || [ -z "${API_BASE_URL}" ]; then
    echo -e "${RED}エラー: CDK出力からVITE_API_BASE_URLを抽出できませんでした${NC}"
    exit 1
fi

if [ "${USER_POOL_ID}" = "null" ] || [ -z "${USER_POOL_ID}" ]; then
    echo -e "${RED}エラー: CDK出力からVITE_APP_USER_POOL_IDを抽出できませんでした${NC}"
    exit 1
fi

if [ "${USER_POOL_CLIENT_ID}" = "null" ] || [ -z "${USER_POOL_CLIENT_ID}" ]; then
    echo -e "${RED}エラー: CDK出力からVITE_APP_USER_POOL_CLIENT_IDを抽出できませんでした${NC}"
    exit 1
fi

if [ "${REGION}" = "null" ] || [ -z "${REGION}" ]; then
    echo -e "${RED}エラー: CDK出力からVITE_APP_REGIONを抽出できませんでした${NC}"
    exit 1
fi

echo -e "${GREEN}パラメータの抽出に成功しました:${NC}"
echo -e "  API Base URL: ${API_BASE_URL}"
echo -e "  User Pool ID: ${USER_POOL_ID}"
echo -e "  User Pool Client ID: ${USER_POOL_CLIENT_ID}"
echo -e "  Region: ${REGION}"
echo ""

# .env.localファイルを作成
ENV_FILE="${PROJECT_ROOT}/frontend/.env.local"
echo -e "${YELLOW}.env.localファイルを作成しています: ${ENV_FILE}${NC}"

cat > "${ENV_FILE}" << EOF
# API設定
VITE_API_BASE_URL=${API_BASE_URL}

# Cognito認証設定
VITE_APP_USER_POOL_ID=${USER_POOL_ID}
VITE_APP_USER_POOL_CLIENT_ID=${USER_POOL_CLIENT_ID}
VITE_APP_REGION=${REGION}
EOF

echo -e "${GREEN}.env.localファイルを作成しました。${NC}"
echo ""

# APIの疎通確認
echo -e "${YELLOW}APIの疎通確認を行っています...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "${API_BASE_URL}" | grep -q "403\|401"; then
    echo -e "${GREEN}APIに接続できました（認証が必要です）${NC}"
elif curl -s -o /dev/null -w "%{http_code}" "${API_BASE_URL}" | grep -q "200"; then
    echo -e "${GREEN}APIに接続できました！${NC}"
else
    echo -e "${RED}警告: APIに接続できませんでした。${NC}"
    echo -e "${YELLOW}APIがデプロイされていることを確認してください。${NC}"
fi

echo -e "\n${GREEN}=== 設定完了 ===${NC}"
echo -e "${YELLOW}フロントエンドアプリケーションを起動します...${NC}"
echo ""

# フロントエンドディレクトリに移動して起動
cd "${PROJECT_ROOT}/frontend"
npm run dev
