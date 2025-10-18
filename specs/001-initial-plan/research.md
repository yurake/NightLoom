# NightLoom MVP診断体験 - Research Log

## Overview
NightLoom MVP の設計に先立ち、要件ドキュメント（docs/requirements/overview.md）および設計資料（docs/design/overview.md 他）を精読し、技術的な判断や未確定事項を整理した。以下は主要な意思決定と根拠、検討した代替案である。

---

### Decision 1: セッション情報はメモリ内ストアで管理し、永続化しない
- **Rationale**: 要件で「セッション内のみの一時データ保持（永続化なし）」と明記され、結果画面表示後は速やかに破棄することでプライバシーと再診断の独立性を担保する。
- **Alternatives considered**:
  - SQLite / Redis などの外部ストア：将来の履歴比較機能で検討予定だが、MVPでは要件外。
  - ブラウザ永続ストレージ：プライバシー要件と矛盾するため不採用。

### Decision 2: LLM 呼び出しは 1 回再試行後、即フォールバック資材を返却する
- **Rationale**: docs/design/llm-client-failover.md に従い、再試行1回＋フォールバック資材で高速な回復を実現する。診断を中断させないことがMVPの価値に直結する。
- **Alternatives considered**:
  - 無制限再試行：応答遅延とコストが増大しUXが悪化。
  - 事前生成キャッシュのみ：ユーザー毎の動的体験が提供できない。

### Decision 3: パフォーマンス計測はAPIレイテンシ（p95）とフォールバック発生率を中心に収集する
- **Rationale**: 要件でシーン取得≤800ms、結果生成≤1.2s、全体≤4.5sが指定されており、FR-011でログ/メトリクス収集が義務化されているため。
- **Alternatives considered**:
  - 平均値のみ計測：ピーク性能が見えず、品質保証に不足。
  - 外部APM導入をMVPで実施：初期コストが高く、ログ/メトリクス基盤で十分。

### Decision 4: UI テーマはセッション開始時の themeId に基づき、結果画面まで一貫適用する
- **Rationale**: docs/design/overview.md §3.5 と frontend-result-screen.md でテーマ一貫性が強調されている。結果画面にも同じ themeId を使用し没入感を維持する。
- **Alternatives considered**:
  - 結果画面のみ別テーマ：一貫性が損なわれ、ストーリー没入感が低下。
  - テーマ機能自体を無効化：将来拡張（FR-026）への布石がなくなる。

### Decision 5: Clarification-results.md を Phase 0 で作成し、Spec との差分を随時追記する
- **Rationale**: 憲章の Spec-First Delivery 原則に従い、曖昧性解消を可視化する。現在は未作成のため、本フェーズで初版を生成する。
- **Alternatives considered**:
  - Clarification を plan 完了後にまとめて実施：後工程での手戻りリスクが高い。
  - Clarification ファイルを省略：憲章違反であり許容できない。

### Decision 6: セッションID は UUIDv4 を採用し、推測困難性要件（NFR-SEC-002）を満たす
- **Rationale**: docs/requirements/overview.md §18 で一時的に UUIDv4 仮採用とある。実装が容易で既存テスト戦略にも組み込み済み。
- **Alternatives considered**:
  - ULID/NanoID：順序保証や短さは利点だが、現時点で追加メリットが小さい。
  - 自前乱数：バグリスクとテスト工数が増える。

---

## Outstanding Clarifications
現時点で仕様から導出可能な不明点はない。Phase 0 の出力として `clarification-results.md` を生成し、将来の質問が生じた場合は同ファイルに追記する。
