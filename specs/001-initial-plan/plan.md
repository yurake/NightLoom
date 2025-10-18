# Implementation Plan: NightLoom MVP診断体験

**Branch**: `001-initial-plan` | **Date**: 2025-10-14 | **Spec**: [specs/001-initial-plan/spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-initial-plan/spec.md`

## Summary

NightLoom のMVPは、4シーン構成の診断フローでユーザーの意思決定傾向を観測し、動的に生成した評価軸とタイプ分類を結果画面で提示する体験を提供する。バックエンド（FastAPI + Python 3.12）とフロントエンド（Next.js 14 + TypeScript）を組み合わせ、LLMとの連携とフォールバック資材を活用して高速かつ安定した診断セッションを実現する。

## Technical Context

**Language/Version**: Python 3.12（backend）、TypeScript 5 / Next.js 14（frontend）  
**Primary Dependencies**: FastAPI、httpx、Pydantic、uv、React 18、Tailwind CSS、pnpm、Playwright  
**Storage**: セッション内メモリ保持（MVPでは永続化なし）  
**Testing**: pytest + httpx/respx、Jest + Testing Library、Playwright  
**Target Platform**: Web SPA（モバイル360px以上〜デスクトップ）  
**Project Type**: Webアプリケーション（backend + frontend モノレポ）  
**Performance Goals**: シーン取得 p95 ≤ 800ms、結果生成 p95 ≤ 1.2s、セッション完了 p95 ≤ 4.5s
**Constraints**: セッションデータは非永続、LLM失敗時フォールバック必須、アクセシビリティ（ARIA/キーボード順）、360px以上レスポンシブ対応
**Scale/Scope**: 同時セッション10件想定、MVP画面6枚（初期プロンプト + シーン×4 + 結果）

## Constitution Compliance Enhancement

### C004: Performance Measurement Implementation
**Target**: p95レイテンシ < 2s保証のための実装計画

#### Performance Metrics Collection System
- **Web Vitals Integration**:
  - First Contentful Paint (FCP) < 1.8s
  - Largest Contentful Paint (LCP) < 2.5s
  - First Input Delay (FID) < 100ms
  - Cumulative Layout Shift (CLS) < 0.1
- **Custom Metrics**:
  - セッション開始～最初のシーン表示: p95 < 800ms
  - シーン遷移時間: p95 < 300ms
  - 結果生成時間: p95 < 1.2s
  - セッション全体完了時間: p95 < 4.5s

#### Real-Time Monitoring Infrastructure
- **Backend Instrumentation** (`backend/src/services/observability.py`):
  ```python
  # Request timing middleware
  - HTTPSレイテンシ計測（開始～終了）
  - LLM呼び出し時間（成功/失敗別）
  - フォールバック発動時間
  - メモリ使用量監視
  ```
- **Frontend Performance Tracking** (`frontend/src/services/performance.ts`):
  ```typescript
  // Performance observer for Web Vitals
  - リアルタイムメトリクス収集
  - セッション単位のパフォーマンス追跡
  - 異常検知とアラート送信
  ```

#### Performance Logging System
- **Log Format**: JSON構造化ログで以下を記録
  - `session_id`, `endpoint`, `duration_ms`, `p95_threshold`, `status`
  - LLMフォールバック有無、エラーコード、メトリクス
- **Retention**: 7日間保持、集計後は破棄（データミニマリズム準拠）

### C002: Session Ephemerality Implementation
**Target**: セッション完全破棄のための技術的担保

#### Automatic Session Destruction
- **Session Lifecycle Management** (`backend/src/services/session.py`):
  ```python
  # セッション自動破棄タイマー
  - 結果表示後30秒で自動破棄
  - 非アクティブセッション10分でタイムアウト
  - メモリリーク防止のためのガベージコレクション
  ```
- **Memory Cleanup Strategy**:
  - セッションデータの完全削除（参照切断）
  - 一時ファイル・キャッシュの即座削除
  - プロセス間共有メモリの安全な解放

#### Data Complete Destruction
- **Frontend Session Management** (`frontend/src/state/SessionContext.tsx`):
  ```typescript
  // ブラウザ履歴とセッション状態の完全削除
  - localStorage/sessionStorageの即座クリア
  - React状態の強制リセット
  - 画面遷移時の前セッション痕跡除去
  ```
- **Privacy Protection Mechanisms**:
  - セッション間のデータ漏洩防止
  - ブラウザキャッシュの確実な無効化
  - 戻るボタンでの旧結果表示阻止

#### Garbage Collection System
- **Memory Management** (`backend/src/services/session_store.py`):
  - WeakRefを活用した自動参照削除
  - 定期実行バックグラウンドタスクでの掃除
  - セッション終了イベントでの即座削除

### Performance Guarantees Technical Implementation
#### Monitoring & Alert System
- **Performance Dashboard**: リアルタイムp95レイテンシ監視
- **Threshold Alerts**: 2s超過時の即座通知
- **Degradation Detection**: 性能劣化の自動検知
- **Session Leak Monitoring**: セッション漏洩の監視

#### Comprehensive Monitoring Infrastructure
**Real-Time Performance Monitoring** (`backend/src/services/monitoring.py`):
```python
# Performance monitoring system
- HealthCheck: エンドポイント生存監視（30秒間隔）
- LatencyTracker: p95レイテンシリアルタイム計算
- AlertManager: 閾値超過時の即座通知
- MetricsAggregator: 1分間隔での統計集計
```

**Alert Configuration**:
- **Warning Level**: p95 > 1.8s（黄色アラート）
- **Critical Level**: p95 > 2.0s（赤色アラート・緊急対応）
- **Session Leak**: アクティブセッション > 15件（メモリ監視）
- **Availability**: 5分間連続エラーで可用性アラート

**Automated Response System**:
- 性能劣化検知時の自動フォールバック切替
- セッション漏洩検知時の強制ガベージコレクション
- 連続エラー時の新規セッション受付停止

#### Charter Compliance Verification
- **Performance Guarantees**: p95 < 2s実装保証の技術的裏付け
- **Session Ephemerality**: 完全破棄の技術的担保
- **Data Minimalism**: 不要データの確実削除
- **Observability**: 全メトリクス監視と自動復旧機構

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Enhanced Charter Compliance Status

- [x] **Spec-First Delivery**: `specs/001-initial-plan/spec.md` を唯一の基準とし、Phase 0 で clarifications 結果を `clarification-results.md` に同期することを計画。

- [x] **Session Ephemerality & Data Minimalism**:
  - **C002準拠**: FR-008強化でセッション自動破棄（30秒）・完全削除・永続化防止を実装
  - **技術保証**: WeakRef活用、ガベージコレクション、メモリクリーンアップ
  - **プライバシー**: セッション間漏洩防止、ブラウザ履歴削除、キャッシュ無効化

- [x] **Resilient AI Operations**: LLM再試行・フォールバック・観測ログ（FR-007, FR-011）を実装に織り込み、リスク対策を定義。

- [x] **Performance & Responsiveness Guarantees**:
  - **C004準拠**: p95 < 2s憲章原則の実装保証を技術仕様で具体化
  - **計測システム**: Web Vitals + カスタムメトリクス + リアルタイム監視
  - **アラート体制**: 2s超過時即座通知、性能劣化自動検知、SLA監視

- [x] **Test & Observability Discipline**: pytest/Jest/Playwright を活用したテスト層とフォールバック監視メトリクスを本計画で整備する。

### Charter Compliance Rate: 100%
**Enhanced Verification**: 全憲章原則に対する技術的実装保証を完備

#### C004 Performance Guarantees Compliance
- ✅ **p95 < 2s実装保証**: Web Vitals + カスタムメトリクス監視
- ✅ **リアルタイム監視**: 1分間隔p95計算、閾値超過即座アラート
- ✅ **自動復旧**: 性能劣化時フォールバック切替、負荷制限

#### C002 Session Ephemerality Compliance
- ✅ **自動破棄**: 結果表示後30秒、非アクティブ10分でタイムアウト
- ✅ **完全削除**: WeakRef + ガベージコレクション + メモリクリア
- ✅ **永続化防止**: データベース書き込み禁止、ファイル保存阻止

#### Data Minimalism & Privacy Protection
- ✅ **7日保持後破棄**: ログローテーション、集計後削除
- ✅ **個人情報非収集**: セッションID以外の識別子なし
- ✅ **ログマスキング**: ユーザー入力の部分マスキング処理

#### Resilient Operations & Observability
- ✅ **フォールバック完全実装**: LLM失敗時即座切替、品質保証
- ✅ **再試行メカニズム**: 1回再試行後フォールバック適用
- ✅ **観測ログ完全実装**: 構造化JSON、エラー追跡、パフォーマンス分析

## Project Structure

### Documentation (this feature)

```
specs/001-initial-plan/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md  (後続フローで生成)
```

### Source Code (repository root)

```
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── clients/
│   └── config/
└── tests/

frontend/
├── src/
│   ├── app/
│   ├── components/
│   ├── services/
│   └── theme/
└── tests/
    ├── unit/
    └── e2e/

shared/            # タイプ/スキーマ共有予定
docs/              # 要件・設計ガイド
```

**Structure Decision**: Webアプリ構成（`backend/` + `frontend/`）を維持し、LLM連携やフォールバック資材は backend/services 配下、UIテーマと状態管理は frontend/src/app 配下で実装する。共有スキーマは将来的に `shared/` へ集約する。

## Complexity Tracking

（該当なし）

---

## Phase 0 – Research Workflow

1. `docs/requirements/overview.md` と `docs/design/overview.md` を精読し、LLMフォールバック・セッション管理・パフォーマンス指標を確認。
2. `specs/001-initial-plan/clarification-results.md` に曖昧性が追加された場合は直ちに同期。現状は未解決事項なし。
3. 研究ログ（research.md）に以下を記録済み:
   - セッション永続化を見送る判断
   - LLM再試行 + フォールバック戦略
   - パフォーマンス計測と監視項目
   - UIテーマ適用ポリシー
   - UUIDv4 採用理由
4. 追加の不明点が発生した場合は `/specify/scripts/bash/clarify` 系のワークフローを再実行し、3 項目以内に収める。

## Phase 1 – Design & Contracts

- **Data Model**: `data-model.md` にセッション、シーン、選択肢、評価軸、タイプ、テーマのスキーマと状態遷移を定義。
- **API Contracts**: `contracts/session-api.yaml` に OpenAPI 3.1 形式で bootstrap/keyword/scene/result エンドポイントを記述。
- **Quickstart**: `quickstart.md` で backend/frontend のセットアップ手順とテストコマンドを整理。
- **Agent Context**: `.specify/scripts/bash/update-agent-context.sh codex` を実行し、AGENTS.md に最新技術スタックを反映（手動で簡潔に整形）。

### Post-Design Constitution Check

- Spec-First Delivery: research & clarifications が spec と同期済み。  
- Session Ephemerality: データモデルで永続化しない前提を明記済み。  
- Resilient AI Operations: contracts でフォールバック指標（fallbackUsed）を返却、ログ項目も定義。  
- Performance & Responsiveness: quickstart で計測確認方法を案内。  
- Test & Observability: テストコマンドとフォールバック検証手順を quickstart に含めた。

---

## Phase 2 – Planning Handoff

- 次フェーズで `/speckit.tasks` を実行し、ユーザーストーリー単位のタスク分解を行う。
- プレイブック実行前に `clarification-results.md` を確認し、新たな質問があれば先に解決する。
