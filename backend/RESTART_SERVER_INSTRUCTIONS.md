# サーバー再起動とログ確認手順

## 🚨 重要: サーバーが停止しています

ログファイル出力機能を追加したため、サーバーを手動で再起動する必要があります。

## 📋 手順

### 1. サーバー再起動
```bash
cd backend
LOG_LEVEL=DEBUG OPENAI_LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. ログファイル確認テスト実行
別のターミナルで：
```bash
cd backend
python test_with_log_file.py
```

### 3. リアルタイムログ監視
```bash
tail -f backend/logs/nightloom.log
```

## 🔍 確認すべきログパターン

### ✅ 成功時のログ:
```
[Provider Chain] Starting with 3 providers: ['openai', 'anthropic', 'mock']
[Health Check] Mock provider: always healthy
[Provider Chain] ✓ Success with mock (attempt 3)
[Mock] Generated keywords: ['愛情', '明るい', '新しい', '温かい']
```

### ❌ エラー時のログ:
```
AttributeError: 'ProviderConfig' object has no attribute
ValidationError: 1 validation error for ProviderConfig
[Provider Chain] ✗ mock unexpected error
[LLM Service] Using fallback keywords
```

## 🎯 期待される結果

- **ログファイル**: `backend/logs/nightloom.log` に詳細ログが出力
- **API応答**: `fallbackUsed: false`
- **動的生成**: Mockプロバイダーによるキーワード生成成功

## 🔧 トラブルシューティング

もしエラーが継続する場合は、ログファイルの内容を確認して具体的なエラーメッセージを特定してください。

```bash
cat backend/logs/nightloom.log | grep -E "(ERROR|WARN|AttributeError|ValidationError)"
