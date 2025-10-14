<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0
- Modified principles: n/a (新規策定)
- Added sections: Core Principles, Project Constraints, Delivery Workflow, Governance
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ Constitution Gate を原則ベースで更新
  - .specify/templates/spec-template.md ✅ 現行テンプレートで整合
  - .specify/templates/tasks-template.md ✅ テスト/メトリクス必須条件を反映
- Follow-up TODOs: none
-->

# NightLoom Constitution

## Core Principles

### I. Spec-First Delivery
NightLoom の開発は仕様駆動で進める。`specs/` に蓄積された調査・計画・仕様を唯一の真実とし、実装フェーズへ進む前に認証を受けなければならない。
- **Non-negotiable**: 仕様書に記載されたユーザーストーリーと受け入れ条件を満たさないコードはマージ不可。Constitution Check をパスしない限り Phase 0 研究を開始してはならない。
- **Design impact**: 仕様更新は常に `clarification-results.md` や Quality Checklist と同期し、差分があれば追記して可視化する。
- **Rationale**: 仕様ドリフトを防ぎ、セッションごとに変動する AI 出力を一貫した体験に固定するため。

### II. Session Ephemerality & Data Minimalism
ユーザーの診断体験は単一セッション内で完結し、個人情報を保持しない。
- **Non-negotiable**: セッション終了後はサーバー・クライアント双方で結果データを破棄し、永続化や再利用を行ってはならない。
- **Non-negotiable**: 新しい診断開始時は sessionId、結果、テーマなど全てを再生成し、ブラウザバックで過去結果が復活しないよう履歴を置換する。
- **Rationale**: プライバシー保護と再診断時の完全独立性を保証し、意図せぬデータ残留を防ぐ。

### III. Resilient AI Operations
LLM 依存処理は必ず観測とフェイルオーバー戦略を備え、1回の失敗で体験を壊さない。
- **Non-negotiable**: LLM 呼び出しはタイムアウトと再試行を実装し、失敗時にはプリセットシナリオ/タイプで即座に代替する。
- **Non-negotiable**: 生成結果の検証（軸数 2〜6、命名規約、スコア範囲）は必須であり、逸脱を検知した場合はフォールバックを発動する。
- **Rationale**: 推論品質のばらつきと外部 API 障害に耐えることで、NightLoom の結果画面を常に提供できる。

### IV. Performance & Responsiveness Guarantees
ユーザーに対する高速応答を維持し、明示されたパフォーマンス指標を下回らなければならない。
- **Non-negotiable**: 結果画面の初回レンダリングは 500ms 未満、診断全体の完了は 4.5s p95 以下を維持する。これを満たさない変更はリリース不可。
- **Non-negotiable**: 軸スコアアニメーションは 100ms 後に開始し 1s 以内に完了する。「遅延」「jank」が発生する実装は拒否する。
- **Rationale**: 診断プロダクトの没入感は体感速度に左右され、スコア表示の即時性が満足度を決定づけるため。

### V. Test & Observability Discipline
テストと計測は機能と同等に扱い、失敗時の診断が可能な状態を常に保つ。
- **Non-negotiable**: バックエンドは pytest、フロントエンドは Jest + Playwright のテストを用意し、フェイルオーバーや結果レンダリングをカバーする。
- **Non-negotiable**: 重要 API にはレイテンシ、失敗率、フォールバック発動のメトリクスを埋め込み、p95 監視を CI と共有する。
- **Rationale**: 変動する LLM とリアルタイム UI を安定運用するには、テストピラミッドと観測データの両輪が不可欠。

## Project Constraints

- **技術スタック**: バックエンドは Python 3.12 + FastAPI、フロントエンドは Next.js 14 (App Router) + React 18 + Tailwind CSS。テストは pytest/httpx、Jest/Testing Library、Playwright を標準とする。
- **データ方針**: 個人情報は収集せず、診断結果もセッション内の一時データのみ。ログはメトリクス目的に限定し、外部永続化は次期検討事項。
- **AI 連携**: LLM プロンプト/レスポンスは監査可能な形式で保存し、プロバイダ障害時は FallbackProvider で 2 軸プリセットを返却する。
- **UI/UX 要件**: 360px 以上のレスポンシブ対応、アクセシビリティ (ARIA ラベル・キーボードナビゲーション) を最低限保証し、アニメーションは `prefers-reduced-motion` を尊重する。

## Delivery Workflow

1. **Phase 0 - Research**: `specs/[###]/clarification-results.md` に曖昧性を記録し、必要なドメイン入力を全て揃える。Constitution Check を満たすまで進行禁止。
2. **Phase 1 - Design**: `research.md` と `plan.md` にアーキテクチャ・データモデルを反映し、仕様書と相互リンクさせる。AI 依存箇所のメトリクス測定計画をここで確定する。
3. **Phase 2 - Tasks**: `tasks.md` に実装タスクを分解し、各タスクがどの原則を満たすか明示する (例: Test & Observability Discipline → Playwright E2E)。
4. **Compliance Review**: PR レビューでは `Quality Checklist` を更新し、全ての Core Principle が守られていることをチェックする。

## Governance

- 本憲章は NightLoom の開発ルールを統合し、他のガイドラインより優先する。逸脱が必要な場合は Issue で議論し、例外と理由を明記する。
- 改訂は以下の手順に従う:
  1. 変更目的と影響範囲を記載した提案を作成 (`docs/notes/` or Issue)。
  2. テンプレート/README 等への波及を評価し、Sync Impact Report に反映する。
  3. `/specify/memory/constitution.md` を更新し、Semantic Versioning でバージョンを上げる。
- **Versioning**:  
  - MAJOR: Core Principle の追加・削除、意味変更。  
  - MINOR: セクション追加や実務プロセスの大幅強化。  
  - PATCH: 文言調整や補足説明。
- **Compliance Review**: 各フェーズ終了時に Constitution Check を再実施し、`plan.md`/`tasks.md` に遵守状況を記録する。CI での自動チェックが導入された際は同じ基準を利用する。

**Version**: 1.0.0 | **Ratified**: 2025-10-14 | **Last Amended**: 2025-10-14
