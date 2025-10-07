## 概要
- コマンド `pnpm --filter nightloom-frontend test:e2e` を実行しようとしたところ、ローカル環境で `pnpm` が見つからず停止した。
- Playwright のシナリオ `frontend/e2e/theme.spec.ts` を確認した結果、テーマボタン数の期待値が UI 実装と乖離していることを特定した。

## 詳細
- UI では `Adventure`, `Serene`, `Focus`, `Fallback` の 4 つのテーマボタンを表示している。
- E2E テストは 3 件のみを想定したため、`Fallback` の追加後に失敗する状態となっていた。
- テストを期待仕様に合わせ、4 件のボタン表示と各ラベルの可視性を検証するよう更新した。

## フォローアップ
- Node.js / pnpm を事前にセットした環境で Playwright テストを再実行し、修正の有効性を確認する。
