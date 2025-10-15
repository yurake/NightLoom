# 要件品質チェックリスト: NightLoom MVP診断体験

**目的**: 要件の書き方品質を「ユニットテスト」として検証  
**生成日**: 2025-10-15  
**対象**: [specs/001-initial-plan/spec.md](../spec.md)  
**フォーカス**: 実装ではなく要件文書の品質を評価

---

## 要件完全性チェック

### CHK001: ユーザーストーリー完全性
- [ ] 各ユーザーストーリーにWhy（優先度理由）が明記されているか？ [Spec §User Scenarios]
- [ ] 各ユーザーストーリーにIndependent Test条件が定義されているか？ [Spec §User Scenarios]
- [ ] 全ユーザーストーリーでAcceptance Scenariosが3件以上定義されているか？ [Spec §User Scenarios]
- [ ] エッジケースが各ユーザーストーリーに対応して網羅されているか？ [Spec §Edge Cases]

### CHK002: 機能要件完全性
- [ ] 機能要件FR-001〜FR-012が各ユーザーストーリーの実現に必要十分か？ [Spec §Functional Requirements]
- [ ] 各機能要件に「〜しなければならない」形式の明確な動作が定義されているか？ [Spec §Functional Requirements]
- [ ] データ永続化・破棄に関する要件（FR-008, FR-012）が明確に定義されているか？ [Spec §Functional Requirements]
- [ ] フォールバック要件（FR-007）が失敗条件と対応策を具体的に記述しているか？ [Spec §Functional Requirements]

### CHK003: 成功基準完全性
- [ ] 全成功基準（SC-001〜SC-005）に具体的な数値目標が設定されているか？ [Spec §Success Criteria]
- [ ] SC-003の理解度測定に詳細な測定方法・指標・判定基準が定義されているか？ [Spec §Success Criteria]
- [ ] パフォーマンス指標（p95レイテンシ）が具体的な数値で規定されているか？ [Spec §Success Criteria]
- [ ] 各成功基準が技術実装に依存しない測定可能な形で記述されているか？ [Spec §Success Criteria]

---

## 要件明確性チェック

### CHK004: 用語・概念明確性
- [ ] Key Entities（Session, Scene, Choice等）の定義が曖昧さなく記述されているか？ [Spec §Key Entities]
- [ ] 「2〜6軸の動的生成」の軸数決定ロジックが明確に定義されているか？ [Spec §FR-005]
- [ ] 「4〜6種類のタイプ」の種類数決定条件が明確に定義されているか？ [Spec §FR-006]
- [ ] テーマID（serene, adventure, focus等）の選択基準が明確に定義されているか？ [Spec §Data & Content Requirements]

### CHK005: 状態遷移明確性
- [ ] セッション状態（INIT/PLAY/RESULT）の遷移条件が明確に定義されているか？ [Spec §Key Entities]
- [ ] 各状態で許可される操作と禁止される操作が明確に定義されているか？ [Spec §FR-002, FR-004]
- [ ] 状態遷移の失敗条件とエラーハンドリングが明確に定義されているか？ [Spec §Edge Cases]
- [ ] セッション終了・破棄のタイミングと条件が明確に定義されているか？ [Spec §FR-008, FR-012]

### CHK006: 入出力明確性
- [ ] 各APIエンドポイントの入力パラメータ制約が明確に定義されているか？ [Spec §FR-001〜FR-012]
- [ ] レスポンス形式（JSON構造）が明確に定義されているか？ [Spec §FR-004, FR-006]
- [ ] バリデーションエラーの条件と応答が明確に定義されているか？ [Spec §Edge Cases]
- [ ] 正規化スコア（0〜100）の計算ロジックが明確に定義されているか？ [Spec §Data & Content Requirements]

---

## 要件一貫性チェック

### CHK007: ユーザーストーリー間一貫性
- [ ] ユーザーストーリー1-3の優先度（P1-P3）が相互依存関係と整合しているか？ [Spec §User Scenarios]
- [ ] 各ストーリーのIndependent Test条件が他ストーリーと矛盾していないか？ [Spec §User Scenarios]
- [ ] セッション開始〜結果表示の一連フローが3ストーリー間で一貫しているか？ [Spec §Experience Flow]
- [ ] エッジケース対応が全ユーザーストーリーで一貫した方針で定義されているか？ [Spec §Edge Cases]

### CHK008: 機能要件間一貫性
- [ ] FR-003のスコア累積とFR-004の正規化処理が数値的に整合しているか？ [Spec §Functional Requirements]
- [ ] FR-005の軸生成とFR-006のタイプ生成で使用する軸が一貫しているか？ [Spec §Functional Requirements]
- [ ] FR-007のフォールバック適用条件が他要件と矛盾していないか？ [Spec §Functional Requirements]
- [ ] FR-011の観測ログ項目がFR-007のフォールバック要件と一貫しているか？ [Spec §Functional Requirements]

### CHK009: 成功基準と要件の一貫性
- [ ] SC-001の完了時間とPerformance Targetsの指標が整合しているか？ [Spec §Success Criteria vs Performance Targets]
- [ ] SC-002の完了率とFR-007のフォールバック要件が整合しているか？ [Spec §Success Criteria vs Functional Requirements]
- [ ] SC-005のレイテンシ目標とPerformance Targetsの値が一致しているか？ [Spec §Success Criteria vs Performance Targets]
- [ ] 成功基準の測定方法が機能要件で実現可能な内容になっているか？ [Spec §Success Criteria vs Functional Requirements]

---

## 受入基準品質チェック

### CHK010: 受入シナリオ測定可能性
- [ ] Given-When-Then形式のシナリオで条件・動作・結果が具体的に記述されているか？ [Spec §Acceptance Scenarios]
- [ ] 「セッションID・初期文字・候補単語が提示される」などの結果が検証可能か？ [Spec §User Story 1 Scenarios]
- [ ] 「シーンn+1がロードされ進行状況が更新される」などの状態変化が測定可能か？ [Spec §User Story 2 Scenarios]
- [ ] 「タイプ名・説明・キーワード・2〜6評価軸スコアが全て表示される」などの要素が検証可能か？ [Spec §User Story 3 Scenarios]

### CHK011: エラーケース受入基準
- [ ] 「LLMの初期生成失敗」時の既定資材表示が測定可能な基準で定義されているか？ [Spec §User Story 1 Scenario 3]
- [ ] 「ネットワーク遅延」時のローディング表示とタイムアウト処理が測定可能か？ [Spec §User Story 2 Scenario 2]
- [ ] 「タイプ生成で閾値判定が揺らぐ」場合の再試行・プリセット適用が測定可能か？ [Spec §User Story 3 Scenario 3]
- [ ] 各エラーケースの復旧条件と成功状態が明確に定義されているか？ [Spec §Edge Cases]

### CHK012: パフォーマンス受入基準
- [ ] 「4.5秒以内での完了」が具体的な開始・終了条件で定義されているか？ [Spec §SC-001]
- [ ] 「p95レイテンシ≤800ms/1.2s」の測定ポイントが明確に定義されているか？ [Spec §Performance Targets]
- [ ] 「同時稼働セッション10件」での性能維持条件が測定可能か？ [Spec §Performance Targets]
- [ ] タイムアウト・遅延時の許容範囲と警告条件が数値で定義されているか？ [Spec §Edge Cases]

---

## シナリオカバレッジチェック

### CHK013: 正常フローカバレッジ
- [ ] セッション開始→キーワード選択→4シーン完走→結果表示の完全フローが定義されているか？ [Spec §Experience Flow]
- [ ] 候補選択と自由入力の両パターンがシナリオでカバーされているか？ [Spec §User Story 1]
- [ ] 各シーン（1-4）での選択→次シーン遷移が全てカバーされているか？ [Spec §User Story 2]
- [ ] 結果表示→再診断の循環フローがシナリオでカバーされているか？ [Spec §User Story 3]

### CHK014: 分岐・変動ケースカバレッジ
- [ ] 軸数の変動（2-6軸）パターンがシナリオでカバーされているか？ [Spec §FR-005]
- [ ] タイプ数の変動（4-6種類）パターンがシナリオでカバーされているか？ [Spec §FR-006]
- [ ] テーマ選択の多様性（serene/adventure/focus/fallback）がカバーされているか？ [Spec §Data & Content Requirements]
- [ ] スコア分布の極端ケース（全軸同値等）がカバーされているか？ [Spec §Data & Content Requirements]

### CHK015: 異常・エラーフローカバレッジ
- [ ] LLM API失敗からフォールバック適用までのフローが定義されているか？ [Spec §FR-007]
- [ ] 無効セッションID・期限切れアクセスのエラーフローが定義されているか？ [Spec §Edge Cases]
- [ ] 入力バリデーション失敗（禁止語・文字数）のエラーフローが定義されているか？ [Spec §Edge Cases]
- [ ] ネットワーク断・タイムアウト時の復旧フローが定義されているか？ [Spec §Edge Cases]

---

## エッジケース品質チェック

### CHK016: 境界条件定義
- [ ] 軸数の境界（2未満・6超過）での自動縮退条件が明確に定義されているか？ [Spec §Edge Cases]
- [ ] スコア範囲の境界（-5.0/5.0, 0/100）での処理が明確に定義されているか？ [Spec §Data & Content Requirements]
- [ ] 文字数制限（キーワード1-20文字）の境界処理が明確に定義されているか？ [Spec §Edge Cases]
- [ ] レイテンシ閾値（800ms/1.2s/5s）超過時の処理が明確に定義されているか？ [Spec §Performance Targets]

### CHK017: 互換性・アクセシビリティエッジケース
- [ ] モバイル（360px幅）でのUI崩れ防止条件が明確に定義されているか？ [Spec §Edge Cases]
- [ ] `prefers-reduced-motion`ユーザー向けアニメーション抑制が明確に定義されているか？ [Spec §Edge Cases]
- [ ] キーボードナビゲーション・スクリーンリーダー対応条件が明確に定義されているか？ [Spec §FR-010]
- [ ] 異なるブラウザ・デバイスでの動作保証範囲が明確に定義されているか？ [Spec §Resilience & Compliance Requirements]

### CHK018: セキュリティ・プライバシーエッジケース
- [ ] セッションID推測困難性・無効ID処理が明確に定義されているか？ [Spec §Resilience & Compliance Requirements]
- [ ] 個人情報非収集・データ破棄条件が明確に定義されているか？ [Spec §Resilience & Compliance Requirements]
- [ ] 入力サニタイゼーション・禁止語フィルタが明確に定義されているか？ [Spec §Edge Cases]
- [ ] セッション乗っ取り・不正アクセス防止策が明確に定義されているか？ [Spec §Edge Cases]

---

## 要件品質サマリー

**チェック観点**: 18項目 / 72チェックポイント  
**フォーカス領域**: UX要件品質、API要件品質、パフォーマンス要件品質、セキュリティ要件品質  
**品質基準**: 全チェックポイント通過で要件品質「合格」と判定

**次のステップ**: 
1. 各チェックポイントを個別に検証
2. 不合格項目の要件修正提案
3. 品質向上のための具体的改善案の作成
4. 要件レビュー会議での品質確認

**使用方法**:
- 要件レビュー時にチェックリストとして活用
- 実装開始前の品質ゲートとして使用
- 仕様変更時の影響範囲確認に使用
- プロダクトオーナーとの合意形成に使用

**注意事項**:
- このチェックリストは要件文書の品質を検証するものであり、実装の正確性は別途テストで確認
- 全項目の完全チェックが必須ではないが、重要項目（CHK001-CHK006）は必須確認
- 品質向上は段階的に進め、一度にすべての改善を求めない
