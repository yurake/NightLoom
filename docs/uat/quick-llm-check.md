# NightLoom 生成AI機能 クイックUAT手順書

約1分で完了するNightLoom生成AI機能の基本動作確認手順です。

## 対象機能
- キーワード生成（LLM）
- シーン生成（LLM）
- 診断結果生成
- フォールバック機能

## 事前準備（約30秒）

### 1. 環境変数・API設定確認
```bash
# 必要な環境変数が設定されているか確認
echo $OPENAI_API_KEY  # OpenAI APIキーが設定されている場合
echo $ANTHROPIC_API_KEY  # Anthropic APIキーが設定されている場合
```

### 2. サーバー起動確認
```bash
# バックエンドサーバーが起動しているか確認
curl -s http://localhost:8000/health
# 期待レスポンス: {"status":"ok"}

# フロントエンドサーバーが起動しているか確認（別ターミナルで）
curl -s http://localhost:3000 | head -5
```

## 生成AI機能のクイックテスト（約30秒）

### 1. キーワード生成APIテスト
```bash
# セッション開始・キーワード生成
curl -X POST http://localhost:8000/api/sessions/start \
  -H "Content-Type: application/json" \
  -d '{"initial_character": "あ"}' | jq

# 確認ポイント:
# - sessionId が UUID形式で返る
# - keywordCandidates に4個のキーワードが含まれる
# - fallbackUsed フラグの値（false=LLM成功、true=フォールバック使用）
```

**期待レスポンス例:**
```json
{
  "sessionId": "12345678-1234-1234-1234-123456789abc",
  "keywordCandidates": ["あい", "あたたかい", "あかるい", "あたらしい"],
  "initialCharacter": "あ",
  "themeId": "adventure",
  "fallbackUsed": false
}
```

### 2. シーン生成APIテスト
```bash
# 取得したsessionIdを使用（上記レスポンスから）
SESSION_ID="12345678-1234-1234-1234-123456789abc"

# キーワード確定・最初のシーン生成
curl -X POST http://localhost:8000/api/sessions/$SESSION_ID/keyword \
  -H "Content-Type: application/json" \
  -d '{"keyword": "あい", "source": "suggestion"}' | jq

# 確認ポイント:
# - scene.narrative にシーンの説明文が含まれる
# - scene.choices に選択肢が含まれる
# - fallbackUsed フラグの値
```

### 3. 診断結果生成APIテスト（簡易版）
```bash
# セッション進行状況確認
curl -X GET http://localhost:8000/api/sessions/$SESSION_ID/result/status | jq

# 確認ポイント:
# - completedScenes の値
# - readyForResult フラグ
# - fallbackFlags の内容
```

## フロントエンド動作確認（約30秒）

### 1. ブラウザでの基本フロー
1. `http://localhost:3000` を開く
2. テーマを選択して「診断を開始」をクリック
3. キーワード候補が表示されることを確認
4. 任意のキーワードをクリック
5. シーンと選択肢が表示されることを確認

### 2. 確認ポイント
- [ ] 初期文字「あ」でキーワード候補が生成される
- [ ] 選択したキーワードでシーンが開始される
- [ ] ナラティブ文が自然な日本語で表示される
- [ ] 選択肢が適切に表示される
- [ ] ローディング状態が適切に表示される

## 総合確認ポイント

### LLM API正常応答
- [ ] OpenAI/Anthropic APIが正常に応答している
- [ ] エラーログが出力されていない
- [ ] レスポンス時間が適切（通常2-5秒以内）

### 生成コンテンツ妥当性
- [ ] キーワードが指定した初期文字で始まっている
- [ ] シーンの内容が自然で理解しやすい
- [ ] 選択肢が適切でバリエーションがある

### フォールバック機能動作
- [ ] LLM APIエラー時にフォールバック資産が使用される
- [ ] `fallbackUsed: true` フラグが正しく設定される
- [ ] フォールバック使用時でも機能が継続する

### エラー状況・異常系
- [ ] API呼び出しエラーが適切にハンドリングされる
- [ ] ネットワークエラー時に適切なメッセージが表示される
- [ ] 無効なセッションIDでの適切な404レスポンス

## トラブルシューティング

### よくある問題
1. **`fallbackUsed: true` が常に表示される**
   - 環境変数 `OPENAI_API_KEY` または `ANTHROPIC_API_KEY` が設定されているか確認
   - APIキーが有効で、クォータが残っているか確認

2. **シーンが表示されない**
   - セッションIDが正しく引き継がれているか確認
   - コンソールエラーログを確認

3. **キーワードが初期文字で始まらない**
   - プロンプトテンプレートの設定を確認
   - LLMレスポンスのパース処理を確認

### 詳細テスト
より詳細なテストが必要な場合:
- [`backend/test_llm_health_check.py`](../backend/test_llm_health_check.py) を実行
- [`backend/test_keyword_generation.py`](../backend/test_keyword_generation.py) を実行

## 期待所要時間
- 事前準備: 30秒
- API直接テスト: 30秒  
- フロントエンド確認: 30秒
- **合計: 約1分30秒**

## 実行例
```bash
# 全体フロー実行例
echo "=== NightLoom LLM クイックチェック ===" && \
curl -s http://localhost:8000/health && echo " ✓ Backend OK" && \
curl -X POST http://localhost:8000/api/sessions/start -H "Content-Type: application/json" -d '{}' | jq '.fallbackUsed' && \
echo "✓ フロントエンド http://localhost:3000 で動作確認してください"
```

---
**注意:** このクイック手順書は開発・テスト環境での基本動作確認用です。本格的な品質保証テストには追加の詳細テストが必要です。
