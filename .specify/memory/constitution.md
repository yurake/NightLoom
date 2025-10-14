<!-- 
Sync Impact Report:
- Constitution updated with NightLoom project-specific values
- All placeholders replaced with concrete project information
- Version set to 1.0.0 as initial constitution
- Ratification date: 2025-10-14
- Aligned with project's Japanese language preference and development practices
-->

# NightLoom Constitution

## Core Principles

### I. 日本語統一
言語は日本語で統一し、コメントで過去の変更に言及しない。
ドキュメント、コード、コミットメッセージすべて日本語を基本とする。

### II. TDD原則（テスト→実装→パス）
TDD必須：テスト作成 → ユーザー承認 → テスト失敗 → 実装の順序を厳守する。
Red-Green-Refactorサイクルを必ず遵守する。

### III. ライブラリ優先
すべての機能は独立したライブラリとして開始する。
ライブラリは自己完結し、独立してテスト可能で、文書化されている必要がある。
明確な目的が必要 - 組織化のためだけのライブラリは作成しない。

### IV. CLIインターフェース
すべてのライブラリは機能をCLI経由で公開する。
テキスト入出力プロトコル：stdin/args → stdout、エラー → stderr。
JSONと人間が読める形式の両方をサポートする。

### V. 統合テスト必須
統合テストが必要な重点領域：新規ライブラリ契約テスト、契約変更、サービス間通信、共有スキーマ。
システム全体の結合部分は必ず統合テストで検証する。

## 技術制約

**技術スタック**：
- バックエンド：Python 3.12、FastAPI
- フロントエンド：Next.js 14、React 18、TypeScript、Tailwind CSS
- テスト：pytest、Jest、Playwright
- パッケージ管理：uv、pnpm

**観測性**：
テキストI/Oによりデバッグ可能性を確保する。
構造化ログを必須とする。

**バージョニング**：
MAJOR.MINOR.BUILD形式を使用する。
破壊的変更は適切にバージョン管理する。

## 開発ワークフロー

**品質保証**：
- Conventional Commits準拠
- mainブランチ保護とSquash Merge
- すべてのPR/レビューでコンプライアンス確認
- 複雑性には正当化が必要

**設計哲学**：
シンプルに開始し、YAGNI原則を適用する。
開発手順はCONTRIBUTING.mdを参照する。
実施内容や検討事項はdocs/に記録する。

## Governance

憲法はすべての他の慣行に優先する。
憲法の修正には文書化、承認、移行計画が必要。
すべてのPR/レビューでコンプライアンス確認を実施する。
複雑性は正当化されなければならない。
実行時の開発ガイダンスにはCONTRIBUTING.mdを使用する。

**Version**: 1.0.0 | **Ratified**: 2025-10-14 | **Last Amended**: 2025-10-14
