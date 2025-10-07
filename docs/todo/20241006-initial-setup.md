---
目的: 初期リポジトリのコミットとリモートへの公開準備
担当者: Codex
関連ブランチ: docs/todo-initial-setup
期限: 2025-10-06
関連Issue: 未作成
---

- [x] ブランチ作成
  - メモ: docs/todo-initial-setup を作成して初期作業を進める
- [x] Issue 作成
  - メモ: 実装タスクは docs/notes/20251006-initial-keyword-api-plan.md と docs/notes/20251006-ui-theme-implementation-plan.md で管理し、定例後に GitHub Issue をまとめて起票予定
- [x] 初期ファイル内容の確認
  - メモ: 規約・ドキュメント構成を精査
- [x] 初期コミットを作成
  - メモ: commit 4639631 (chore(repo): 初期セットアップ)
  - メモ: 必要ファイルをステージングして Conventional Commits 形式で実施
- [x] ドキュメント役割整理
  - メモ: 要件と設計の境界を再構成済み
- [x] 追加要件を反映
  - メモ: 初期単語フローとUIテーマ要件を docs に追記
- [x] 初期キーワード API 実装計画
  - メモ: docs/notes/20251006-initial-keyword-api-plan.md にタスクとスケジュールを整理
- [x] UI テーマ実装計画
  - メモ: docs/notes/20251006-ui-theme-implementation-plan.md に実装フローをまとめた
- [x] リモートへ push
  - メモ: origin/docs/todo-initial-setup へ push 完了
- [x] main ブランチ整備
  - メモ: origin/main を作成しベースブランチの事前準備を整えた
- [ ] PR 作成
  - メモ: GitHub API でのドラフト PR 作成がエラー終了したため、権限設定やベースブランチ構成を確認してから再実施
  - メモ: MCP クライアント `github` が `No such file or directory` で起動せず、Codex CLI でドラフト PR 作成フローを実行できない。`gh` バイナリ導入または CLI 設定修正の要否を確認する
- [x] 実装設計ドキュメント化
  - メモ: docs/design/overview.md §7 に Backend/Frontend/CI の計画を追加済み
- [x] プロジェクト構造設計
  - メモ: docs/design/overview.md §7.0 にモノレポ構成を整理
- [x] バックエンド実装準備
  - メモ: backend/ 配下に FastAPI 雛形と pytest テンプレートを追加
- [x] フロントエンド実装準備
  - メモ: frontend/ 配下に Next.js/Tailwind 雛形と ThemeProvider を追加

## メモ
- 初期コミットに含めるファイルの網羅性を確認する
- docs 配下の参照リンクと実体の差異を後続タスクで補完する
- 要件→設計への情報移管状況を継続監視する
- 初期アクセス起点機能の実装スコープを検討する
