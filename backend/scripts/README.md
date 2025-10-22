# Backend Scripts

このディレクトリには、開発・検証用のスクリプトが含まれています。

## `dev/` - 開発用スクリプト

### 開発サポートツール
- `check_current_status.py` - サーバー状態・API動作確認ツール
- `validate_fallback_keywords.py` - フォールバックキーワード検証ツール

### 注意事項
- これらのスクリプトは開発・デバッグ用途で作成されており、正式なテストスイートには含まれません
- 実行時は `backend` ディレクトリから相対パスで実行してください

### 使用例
```bash
cd backend
uv run python scripts/dev/check_current_status.py
uv run python scripts/dev/validate_fallback_keywords.py
```
