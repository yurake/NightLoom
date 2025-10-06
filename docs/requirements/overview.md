# 性格指向性観測アプリ 要件定義書

## 1. タイトル
性格指向性観測 Web アプリケーション 要件定義 (MVP)

## 2. バージョン / 改訂履歴
| Version | 日付 | 区分 | 記述 | 作成者 |
|---------|------|------|------|--------|
| 0.1.0 (Draft) | 2025-10-06 | 初版 | MVP 初期要件確定 | Team |

## 3. ビジョン
ユーザーが短時間の分岐型シナリオ体験を通じて、自身の行動傾向・意思決定指向性を理解できるようにする。AI により毎セッション動的に評価軸とタイプ分類を生成し、ゲーム的没入と再利用性を両立する。

## 4. スコープ
### 4.1 In Scope (MVP)
- 4シーン × 各4選択肢による単一セッション
- シナリオ/選択肢文面のAI生成（高密度短尺・スピード優先）
- 選択パターン解析（内部スコア加算）
- AI 生成された 2〜6 評価軸スコア (0〜100 正規化)
- ハイブリッド型タイプ分類（評価軸極性組合せ）
- 結果表示（軸スコア一覧 + タイプ名 + タイプ説明）
- フェイルオーバー（再試行 + プリセット固定シナリオ/タイプ）
- Web SPA（PC/モバイル対応）
- セッション内のみの一時データ保持（永続化なし）
### 4.2 Out of Scope (明示的除外)
- ユーザー登録 / 認証
- 履歴保存・再参照
- A/B テスト基盤
- 国際化 (i18n)
- アクセシビリティ詳細指針 (WCAG 適合)
- 課金 / マネタイズ
- 分析用ログの外部蓄積
- ユニーク性重複検証（将来課題）

## 5. 用語定義
| 用語 | 定義 |
|------|------|
| セッション (Session) | start から result 取得までの一連のプレイ単位 |
| シーン (Scene) | 分岐テキスト表示と4つの選択肢セット |
| 選択肢 (Choice) | シーンに提示される行動/回答オプション（常に4） |
| 評価軸 (Axis) | 行動指向性を測る抽象次元（2〜6 個） |
| タイプ (Type) | 主たる2軸の極性組合せより導出される分類ラベル |
| 重みベクトル (Weight Vector) | 各選択肢が各評価軸へ与える加算影響値 |
| 正規化 (Normalization) | 軸スコアを 0〜100 に線形変換する操作 |
| フェイルオーバー | LLM 失敗時の再試行/プリセット切替処理 |
| プリセットタイプ | 失敗時に使用する固定タイプ 6 種 |

## 6. ユースケース概要
### UC-01: 診断プレイ
1. ユーザーがアプリにアクセスし「Start」操作
2. セッション開始 (評価軸生成 + シナリオ初期化)
3. 4 シーンを順番に表示
4. 各シーンでユーザーが1選択肢を選ぶ
5. 内部スコア集計・最終計算
6. タイプ分類・スコア結果表示
7. セッション終了（データ破棄）

### 主要ユーザフロー (単一路線)
start → scene1 → scene2 → scene3 → scene4 → result

## 7. 機能要件 (Functional Requirements)
| ID | 要件 | 説明 | 優先度 |
|----|------|------|--------|
| FR-001 | セッション開始API | 評価軸(2〜6)と初回シーンメタ生成 | High |
| FR-002 | シーン取得API | 指定シーン番号に対応するシナリオ + 4選択肢取得 | High |
| FR-003 | 選択記録 | 各選択で内部スコア加算処理 | High |
| FR-004 | 重みベクトル生成 | 各選択肢に軸重みベクトル付与（AI 生成） | High |
| FR-005 | 評価軸動的生成 | 軸名/説明/重み/方向性決定 | High |
| FR-006 | タイプ分類動的生成 | 軸極性組合せによる 4〜6 タイプ生成 | High |
| FR-007 | タイプ命名制約 | 英語1〜2語, 最大14文字, 重複不可 | High |
| FR-008 | タイプフェイルオーバー | 生成失敗時プリセット6タイプ適用 | High |
| FR-009 | 結果生成API | 正規化スコア + タイプ判定結果返却 | High |
| FR-010 | 正規化処理 | 各軸 0〜100 線形変換 | High |
| FR-011 | 再試行制御 | LLM 失敗時 1 回即時再試行 | High |
| FR-012 | シナリオフェイルオーバー | 再試行失敗時固定シナリオ利用 | High |
| FR-013 | セッション状態管理 | メモリ内 or 一時コンテキスト保持 | Medium |
| FR-014 | 残シーン遷移制御 | 選択確定後 次シーン取得 | High |
| FR-015 | スコア集計 | 重みベクトル逐次加算 | High |
| FR-016 | タイプ極性判定 | 主軸高低閾値で極性 Hi/Lo 算出 | Medium |
| FR-017 | API レイテンシ計測 | p95 計測可能なメトリクス埋め込み | Medium |
| FR-018 | スコア表示UI | 軸スコア + タイプ + 簡易説明表示 | High |
| FR-019 | セッション終了処理 | 結果表示後メモリ破棄 | Medium |
| FR-020 | リクエストバリデーション | 必須パラメータ検証 | High |
| FR-021 | 重複命名検出 | 生成タイプ重複時リネームor再生成 | Medium |
| FR-022 | 軸数範囲保証 | 2〜6 の範囲外生成時リトライ | High |
| FR-023 | 解析ロジック抽象化層 | スコア計算を独立モジュール化 | Medium |
| FR-024 | ログ（最低限） | 障害解析用エラーログ出力（PII 無） | Medium |
| FR-025 | クライアント再取得保護 | result 取得後再度シーン取得不可 | Low |

## 8. 機能外 (Explicit Exclusions)
- 複数同時セッションをユーザー単位で持つ管理
- 過去結果比較
- 詳細レポート (PDF/Export)
- ソーシャルシェア生成画像
- 多言語切替

## 9. シナリオ生成仕様
- シーン数: 固定 4
- 各シーン選択肢: 固定 4
- 文面特性: 高密度 / 読了 ≤ 5 秒想定 / 過剰装飾回避
- コンテキスト: セッション開始時に統一テーマ（AI 任意）
- 出力フォーマット（内部想定例）:
```
{
  "sceneIndex": 1,
  "nChoices": 4,
  "narrative": "短い状況描写",
  "choices": [
    {"id":"c1","text":"行動A","weights":[... axis length ...]},
    ...
  ]
}
```
- 一意性: 現段階で非保証（重複検証未実装）
- フェイルオーバー: 生成失敗 → 再試行1 → 失敗 → 固定プレースホルダシナリオ（付録参照）

## 10. 評価軸生成仕様
- 軸数: 2〜6（乱数またはAI裁量）
- 各軸属性: name, description, weightNormalizationStrategy(optional), direction(HigherIsPositive or HigherIsNegative)
- 重み付与: 選択肢ごと axis_length の整数/小数配列（AI 任意スケール → 後段で正規化）
- 軸名制約: 英語 Camel / Title Case 推奨、長さ上限 20 chars
- 方向性: 極性表示に利用（結果 UI で矢印表示可能）
- 整合性検証: 軸数範囲外 → 再生成 1 回 → 失敗時: 既定2軸 (Exploration, Convergence)

## 11. タイプ分類仕様 (Spec-A)

### 11.1 Purpose
- 動的生成された評価軸 (参照: §10 評価軸生成仕様) のスコア結果から、ユーザー理解を促進する 4〜6 個の「タイプ」を即時合成し、主たる行動指向性を簡潔に伝える。
- 再現性より可読性・分類差異・説明一貫性を優先。
- 出力は結果画面および内部ログで利用。

### 11.2 Inputs & Dependencies
| 入力 | 型 / 範囲 | 説明 |
|------|-----------|------|
| axesMeta | Array<AxisMeta> | 軸名 / 説明 / 方向性 HigherIsPositive/Negative |
| normalizedScores | number[] (0〜100) | 軸順序は axesMeta と同一 |
| axisCount | int (2〜6) | §10 で決定 |
| sessionId | string | ログ相関用 |
| generationConfig | object | 閾値・リトライ設定 |
| rng / llmClient | object | 生成要素（命名・説明） |

AxisMeta: { name: string, direction: enum, description: string }

### 11.3 Constraints & Ranges
| 項目 | 制約 |
|------|------|
| タイプ数 | 4〜6 の整数 → ヒューリスティクス (11.6) |
| 主軸数 | 常に 2 (top2 variance / dispersion) |
| スコア域 | 各軸 0〜100 |
| 動的閾値初期値 | ±10 pt (両側) |
| 動的閾値下限 | 5 pt |
| 命名長 | 1〜14 文字 (英字, スペース除く) |
| 命名語数 | 1〜2 語 (Title Case) |
| 再試行 | LLM 名称生成 1 回まで |
| 重複許容 | 完全一致 / 語幹類似 (stemming) いずれも禁止 |
| 極性組合せ | Hi/Lo × 2 主軸の 4 基本型 + 必要時 中間派生 |

### 11.4 Generation Algorithm
手順概要:
1. 主軸候補計算: 正規化スコア配列の分散寄与度・レンジ差分を指標に順位付け
2. 上位2軸 (axisA, axisB) を選定
3. 各軸に対し動的閾値計算 (11.5)
4. 2軸の Hi/Lo 判定 → 4 基本極性セル (HiHi / HiLo / LoHi / LoLo)
5. スコア分布・極性セル使用率に基づきタイプ数を 4〜6 に拡張 (11.6)
6. 各タイプへ: name 仮生成 → 検証 (11.7) → 衝突時再試行
7. shortDescription (≤60 chars 英語想定可) を LLM かテンプレで生成
8. JSON 出力 (11.8)
9. ログ/メトリクス記録 (11.11)
10. 失敗時フェイルオーバー (11.9)

擬似コード:
```pseudo
function generateTypes(axesMeta, normalizedScores, config):
    assert 2 <= len(axesMeta) <= 6
    rankedAxes = rankAxesByDispersion(normalizedScores)   # variance + range composite
    axisA, axisB = rankedAxes[0], rankedAxes[1]

    thrA = computeDynamicThreshold(normalizedScores[axisA.index], normalizedScores)
    thrB = computeDynamicThreshold(normalizedScores[axisB.index], normalizedScores)

    polarityMap = {}  # axisIndex -> {isHigh: bool}
    for ax in [axisA, axisB]:
        polarityMap[ax.index] = classifyHighLow(normalizedScores[ax.index], thr= ax==axisA ? thrA : thrB)

    baseCells = buildBaseCells(polarityMap)  # 4 fundamental polarity combinations
    targetCount = decideTypeCount(baseCells, normalizedScores, config)  # 4..6

    expandedSet = expandIfNeeded(baseCells, targetCount, normalizedScores)
    types = []
    retries = 0
    usedNames = set()

    for cell in expandedSet:
        name = proposeName(cell, axesMeta, attempt=retries)
        if not validateName(name, usedNames):
            if retries < 1:
                retries += 1
                name = proposeName(cell, axesMeta, attempt=retries)
            else:
                name = fallbackPlainName(cell)  # no suffix pollution
        description = buildShortDescription(cell, axesMeta, polarityMap)
        types.append(buildTypeRecord(name, cell, description))

    if not validateCompleteness(types):
        return fallbackPresetTypes()

    logGenerationMeta(types, axisA, axisB, thrA, thrB)
    return types
```

### 11.5 Polarity & Threshold Logic
- 基本閾値: 初期 ±10pt を基準。
- 全軸スコア集合 S の分散 variance を用いて低分散時は閾値を縮小。
- 動的補正式: $thr = \\max(5, 10 \\times \\sqrt{\\frac{variance}{100}})$
- 判定式 (軸 i の正規化スコア s_i, 全軸平均 μ):
  - High: s_i ≥ μ + thr
  - Low: s_i ≤ μ - thr
  - Neutral: 上記いずれでもない (タイプ補完で 5〜6 個へ拡張時に利用可)
- 2 主軸とも Neutral の場合は、相対差 |s_a - s_b| が thr 超なら大きい方を High, 他方を Low と強制二値化し分類の明瞭性を確保。

### 11.6 Type Count Selection Heuristic
- 基本 4 タイプ (= Hi/Hi, Hi/Lo, Lo/Hi, Lo/Lo)。
- 以下の条件を順次評価し 5 または 6 に拡張:
  1. 条件 Neutral 発生率: (主軸上で High/Low 判定外ユーザー比率想定) が 30% 超 → Neutral 派生 1 追加
  2. 両主軸スコア分布のクラス不均衡 (最小セル期待数 / 最大セル期待数 < 0.35) → 中間差異セル (HighEdge/LowEdge) を 1 追加
  3. 上記 2 条件とも成立し、かつ axisA と axisB の標準偏差差 |σ_a - σ_b| > 8 の場合 → 追加優先セルを高分散軸側に集中 (合計最大 6)
- 追加セルは Neutral 高頻度側を優先。6 超過は切り捨て（発生しない設計）。

### 11.7 Naming Rules & Validation
検証項目 (全て Yes で合格):
| ルール | 判定方法 |
|--------|----------|
| 文字長 ≤ 14 | length(removeSpaces(name)) ≤ 14 |
| 語数 1〜2 | split by space → count ∈ {1,2} |
| 英字のみ (先頭大文字) | Regex: ^[A-Z][a-zA-Z]{2,13}(?:\s[A-Z][a-zA-Z]{2,13})?$ |
| 重複禁止 | case-insensitive set membership |
| 語幹重複禁止 | PorterStem/簡易ステミング後 set 非含有 |
| 禁止語不使用 | 禁止リスト contains? → fail |
| 攻撃的/ネガティブ含意排除 | LLM safety 判定 or 簡易語リスト |
| Fallback 2回失敗時 suffix 不付与 | 再生成2回未満で失敗 → fallbackPlainName |

禁止語例 (拡張可能): ["Bad","Evil","Lazy","Useless","Dummy"]  
語幹重複例: Leader / Leaders → 後者拒否。  
再生成最大 2 回 (初回 + 1 リトライ)。失敗時: 極性記述由来プレーン名 (例: "High Exploration Low Convergence" → 正規化 "ExplorationHigh-ConvergenceLow" → 14 文字超なら略 "ExpHi-ConLo") を整形。

### 11.8 Data Model (JSON Schema サンプル)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GeneratedTypes",
  "type": "object",
  "properties": {
    "algorithmVersion": { "type": "string" },
    "primaryAxes": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 2,
      "maxItems": 2
    },
    "threshold": {
      "type": "object",
      "properties": {
        "axisA": { "type": "number" },
        "axisB": { "type": "number" }
      },
      "required": ["axisA","axisB"]
    },
    "types": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name","primaryAxes","polarityTags","shortDescription"],
        "properties": {
          "name": { "type": "string" },
          "primaryAxes": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 2,
            "maxItems": 2
          },
          "polarityTags": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 1
          },
          "shortDescription": { "type": "string" },
          "meta": {
            "type": "object",
            "properties": {
              "cell": { "type": "string" },
              "isNeutralVariant": { "type": "boolean" }
            }
          }
        }
      },
      "minItems": 4,
      "maxItems": 6
    },
    "generationMeta": {
      "type": "object",
      "properties": {
        "retryCount": { "type": "integer" },
        "fallbackUsed": { "type": "boolean" },
        "variance": { "type": "number" }
      }
    }
  },
  "required": ["algorithmVersion","primaryAxes","threshold","types","generationMeta"]
}
```

### 11.9 Failure & Fallback Flow
フロー:
1. 通常生成試行
2. 命名/重複/不足 (タイプ数 <4) → 1 回再試行
3. 再試行失敗 → プリセット適用 (source="preset")
4. ログ出力 (failure_code=TYPE_PRESET)
5. 出力構造は Data Model に適合

簡易シーケンス:
生成 → 検証(ルール群) → (成功) or (失敗→再試行) → (失敗) → プリセット

プリセット JSON 例:
```json
[
  {"name":"Explorer","primaryAxes":["Exploration","Convergence"],"polarityTags":["Exploration High","Convergence Low"],"shortDescription":"Seeks novelty and breadth"},
  {"name":"Planner","primaryAxes":["Convergence","Exploration"],"polarityTags":["Convergence High","Exploration Low"],"shortDescription":"Structured, plan-oriented"},
  {"name":"Challenger","primaryAxes":["Risk","Stability"],"polarityTags":["Risk High","Stability Low"],"shortDescription":"Pushes boundaries"},
  {"name":"Supporter","primaryAxes":["Harmony","Dominance"],"polarityTags":["Harmony High","Dominance Low"],"shortDescription":"Cooperative facilitator"},
  {"name":"Analyzer","primaryAxes":["Analysis","Impulse"],"polarityTags":["Analysis High","Impulse Low"],"shortDescription":"Logical and methodical"},
  {"name":"Improviser","primaryAxes":["Impulse","Structure"],"polarityTags":["Impulse High","Structure Low"],"shortDescription":"Adaptive and spontaneous"}
]
```

ログコード例 (擬似):
```pseudo
logEvent("TYPE_GENERATION", {
  sessionId,
  algorithmVersion,
  retryCount,
  fallbackUsed,
  thresholdUsed: {axisA: thrA, axisB: thrB},
  discardedNames,
  failureCode?   # nullable
})
```

### 11.10 Examples
例1:
| Axis | Score | 平均差 | 判定 |
|------|-------|--------|------|
| Exploration | 72 | +14 | High |
| Risk | 65 | +7 | (平均差 < thr=10 → Neutral→再二値化: 相対差補正で High) |
| Harmony | 55 | -3 | Neutral |
| Convergence | 38 | -20 | Low |

平均 μ=58. 分散 ≒ 158。thr = max(5, 10 * sqrt(158/100)) ≈ 12.6 → 切上 13。  
Exploration: 72 ≥ 58+13 → High  
Risk: 65 < 71 → Neutral → 相対差 |72-65|=7 < thr → そのまま Neutral (Neutral 派生使用 → タイプ数拡張)  
Convergence: 38 ≤ 58-13 → Low  
主軸: Exploration / Convergence → 基本 4 + Neutral派生1 = 5 タイプ。

タイプ出力例 (抜粋):
| name | polarityTags | 説明(例) |
|------|--------------|----------|
| Trail Seeker | Exploration High / Convergence Low | 広がり優先で収束抑制 |
| Focus Weaver | Exploration High / Convergence High | 発散後構造化 |
| Method Anchor | Exploration Low / Convergence High | 計画重視 |
| Static Observer | Exploration Low / Convergence Low | 低刺激志向 |
| Adaptive Median | Exploration Neutral / Convergence Low | 中庸探索 |

例2 (高分散2軸):
Axes: Risk=82, Stability=30, Analysis=77, Impulse=25  
上位2軸 (Risk, Analysis) → thr ≈ 10 (分散高) → 両方 High → Hi/Hi セル頻度高 → 不均衡回避で Lo/Hi / Hi/Lo 補強 + EdgeVariant 追加 → 6 タイプ。

### 11.11 Logging & Metrics
収集フィールド:
| フィールド | 型 | 説明 |
|-----------|----|------|
| sessionId | string | 相関 ID |
| algorithmVersion | string | 実装バージョン |
| generation_time_ms | int | 型生成処理時間 |
| retry_count | int | 再試行回数 |
| fallback_used | bool | プリセット利用有無 |
| variance | number | 全軸分散 |
| threshold_used.axisA | number | 主軸 A 閾値 |
| threshold_used.axisB | number | 主軸 B 閾値 |
| discarded_names | string[] | 破棄名称一覧 |
| type_count | int | 出力タイプ数 |
| neutral_variant_included | bool | Neutral 派生含有 |
| failure_code | string? | TYPE_PRESET 等 |
| naming_rejection_reasons | string[] | 失敗理由分類 |

メトリクス利用:
- 不均衡検出 (特定セル偏在) → 将来補正アルゴリズム評価
- 閾値感度分析 → 閾値動的式調整（§18 未決項目対応に寄与）

### 11.12 Risks & Mitigations
| リスク | 説明 | 影響 | 緩和策 |
|--------|------|------|--------|
| 過剰類似名称 | 同質語彙により差異認知低下 | UX 低下 | 語幹比較 + 禁止語幹辞書拡張 |
| 不適切名称 | セーフティ逸脱 | ブランド毀損 | LLM safety + 禁止語フィルタ |
| 分散低 (全軸収束) | Hi/Lo 判定不能 | タイプ希薄化 | 動的閾値縮小, Neutral 派生採用 |
| 中立タイプ乱立 | 過剰ニュアンス | 複雑化 | 上限 6, 優先順位選抜 |
| 名称生成失敗 | LLM 応答不良 | 中断 | 再試行 + プレーンフォールバック |
| 不均衡セル | 一部セル利用価値低 | 説得力低 | ヒューリスティク増分 (11.6) |
| 閾値過感度 | 微差で極性ゆらぎ | 再現性不安 | 平滑式 (平方根) で緩和 |
| Neutral 強制二値化誤判 | 境界ケース誤分類 | 納得感低 | 相対差判定 (|s_a - s_b|≥thr) で限定適用 |
| ログ不足 | チューニング困難 | 継続改善停滞 | 11.11 フィールド必須化 |
| 拡張時仕様逸脱 | 上限 >6 拡張時矛盾 | 互換性問題 | Schema versioning |

未決: 高次元 (>6 軸) 時の主軸選定最適化手法 (現状 MVP 範囲外、将来 PCA/情報利得検討)


## 12. スコアリング & 正規化
- 内部スコア初期化: 各軸 0
- raw 集計: 各選択確定ごとに重みベクトル $w_k=(w_{k,1}...w_{k,m})$ を逐次加算し軸 i の生値 $raw_i = \sum_{k=1}^{n} w_{k,i}$
- 正規化: 全軸生値集合 { $raw_i$ } を対象に min/max 抽出し線形変換  
  数式: $score_{norm,i}=\frac{raw_i - min}{max - min} \times 100$  
  例外: 全軸同値 (max=min) の場合は一律 50 とし全軸 Neutral 扱い (タイプ数拡張ヒューリスティク 11.6 に影響)
- 統計補助値: 正規化後配列から平均 $ \mu = \frac{1}{m} \sum_{i=1}^{m} score_{norm,i}$ と分散 $variance = \frac{1}{m} \sum_{i=1}^{m} (score_{norm,i} - \mu)^2$ を算出（§11.5 動的閾値 thr 計算参照）
- 極性判定: Polarity 判定は常に §11.5 の動的閾値 $thr$ を使用 (High/Low/Neutral)。2 主軸とも Neutral の場合の再二値化は §11.5 ロジックに従う
- 出力丸め: 小数第 1 位
- ログ出力: generationMeta.variance, generationMeta.threshold_used.axisA / axisB を記録（§11.11 参照）

## 13. セッションライフサイクル & API エンドポイント案
| フェーズ | 操作 | API 案 | メソッド | リクエスト | レスポンス(主要) |
|---------|------|--------|----------|------------|------------------|
| 開始 | セッション開始 | POST /session/start | POST | {} | {sessionId, axes[], firstScene} |
| シーン取得 | n 番目シーン | GET /session/{id}/scene/{n} | GET | path | {sceneIndex, narrative, choices[]} |
| 選択送信 | 選択反映 | POST /session/{id}/scene/{n}/choice | POST | {choiceId} | {ack:true,nextSceneIndex} |
| 結果取得 | 最終結果 | POST /session/{id}/result | POST | {} | {axesScores[], type, rawScores?} |
| 終了 | 明示破棄(任意) | DELETE /session/{id} | DELETE | path | {ack:true} |

ステート遷移:
STATE_INIT → STATE_PLAY(n=1..4) → STATE_RESULT → STATE_TERMINATED

## 14. フェイルオーバー & 再試行ポリシー
| 対象 | 再試行回数 | 条件 | フォールバック |
|------|------------|------|----------------|
| 軸生成 | 1 | 2〜6 範囲外 or LLM エラー | 既定2軸 (Exploration, Convergence) |
| シナリオ生成 | 1 | LLM エラー | 固定シナリオテンプレ |
| タイプ生成 | 1 | タイプ不足/命名失敗/重複 | プリセット6タイプ |
| ネット/LLM タイムアウト | 0 (即時) | timeout | 直接フォールバック |
- 共通: フォールバック後は追加再試行禁止
- ログ: 原因コード記録 (例: AXIS_FALLBACK, TYPE_PRESET)

## 15. 非機能要件 (NFR)
### 15.1 Performance
| ID | 要件 | 指標 |
|----|------|------|
| NFR-PERF-001 | シーン生成 p95 | ≤ 800ms |
| NFR-PERF-002 | 結果生成 p95 | ≤ 1.2s |
| NFR-PERF-003 | 全セッション(4シーン+結果) p95 | ≤ 4.5s |
| NFR-PERF-004 | 同時セッション 10 維持 | p95 劣化なし |
### 15.2 Reliability
| ID | 要件 | 指標 |
|----|------|------|
| NFR-REL-001 | フェイルオーバー成功率 | > 99% fallback 実行完了 |
| NFR-REL-002 | LLM 失敗検出 | 100% エラーコード付与 |
### 15.3 UX
| ID | 要件 | 指標 |
|----|------|------|
| NFR-UX-001 | 初回操作→結果まで操作回数最小 | 5 クリック以下 |
| NFR-UX-002 | モバイル表示幅対応 | 360px min |
### 15.4 Security/Privacy
| ID | 要件 | 指標 |
|----|------|------|
| NFR-SEC-001 | 個人情報非取得 | 収集フィールド 0 |
| NFR-SEC-002 | セッション ID 推測困難 | ランダム > 64bit |
### 15.5 Maintainability
| ID | 要件 | 指標 |
|----|------|------|
| NFR-MNT-001 | ロジック分離 | スコア計算独立モジュール化 |
| NFR-MNT-002 | 軸/タイプ生成差し替え容易性 | 実装抽象インタフェース化 |
### 15.6 Extensibility
| ID | 要件 | 指標 |
|----|------|------|
| NFR-EXT-001 | 軸数範囲拡張容易 | 上限変更で追加処理改修 ≤ 1 日 |
| NFR-EXT-002 | 永続化追加容易 | Repository 層追加のみで実現 |

## 16. 性能指標
- p95 シーン生成API: ≤ 800ms
- p95 結果生成API: ≤ 1.2s
- p95 セッション合計 (start→result): ≤ 4.5s
- 同時稼働セッション数: 10（上記 p95 維持）
- タイプ分類ロジック CPU 使用: 単回 < 5ms 目安 (想定)

## 17. 制約 & 前提
| 区分 | 内容 |
|------|------|
| 技術 | LLM 外部 API への依存 |
| データ | 永続化なし / 再現性低い |
| コスト | 推論コール数最小化方針（シーン一括 or バッチ） |
| 法的 | 個人情報非取得前提 |
| インフラ | 単一リージョン運用（冗長化初期非対応） |
| キャッシュ | セッション内のみ有効 |

## 18. リスク & 未決事項
| 項目 | 状態 | 理由/影響 | 暫定対応 |
|------|------|-----------|----------|
| ユニーク性検証 | 未決 | 重複体験による鮮度低下 | 将来拡張で差分判定 |
| 軸方向性閾値 | 未決 | Hi/Lo 判定厳格度不確定 | 平均 ±10pt 暫定 |
| LLM コスト上限 | 未決 | コスト最適化基準なし | 利用ログ計測後決定 |
| バッチ生成方式 | 未決 | 1回or逐次生成比較未評価 | MVP は逐次で簡素化 |
| セッションID 生成方式 | 未決 | UUID / ULID / NanoID 選択 | 一時 UUIDv4 仮採用 |
| 語彙フィルタ | 未決 | 不適切語出力リスク | 初期は LLM Safety 任せ |

## 19. 将来拡張 (Future)
- 履歴永続化 / 再比較
- 重複検知 (近似テキスト距離 / hashing)
- 高次元クラスタリング再分類 (Dynamic Typing)
- 多言語対応 (英語 / 他)
- シーン数可変化
- 選択肢難易度調整
- A/B モデル比較
- アクセシビリティ (ARIA, キーボード操作最適化)
- 可視化強化 (レーダーチャート)
- ソーシャルシェア画像生成
- メタ学習による軸提案品質向上

## 20. トレーサビリティ初期マッピング
| FR | 関連仕様 | 備考 |
|----|----------|------|
| FR-001 | 評価軸生成仕様(10), シナリオ生成仕様(9) | |
| FR-002 | シナリオ生成仕様(9) | |
| FR-003 | スコアリング(12,11.5) | 拡張 |
| FR-004 | シナリオ生成仕様(9), スコアリング(12,11.5) | 拡張 |
| FR-005 | 評価軸生成仕様(10) | |
| FR-006 | タイプ分類仕様(11.4,11.5,11.6,11.7) | 拡張 |
| FR-007 | タイプ分類仕様(11.7) | 拡張 |
| FR-008 | タイプ分類仕様(11.9), フェイルオーバー(14) | 拡張 |
| FR-009 | スコアリング(12,11.5), ライフサイクル(13) | 拡張 |
| FR-010 | スコアリング(12,11.5) | 拡張 |
| FR-011 | フェイルオーバー(14), 11.9 | 拡張 |
| FR-012 | フェイルオーバー(14), 11.9 | 拡張 |
| FR-015 | スコアリング(12,11.5) | 拡張 |
| FR-016 | タイプ分類仕様(11.5,11.6), スコアリング(12,11.5) | 拡張 |
| FR-017 | 性能指標(16) | |
| FR-018 | 結果表示UI(7,12,11.4,11.5,11.6) | 拡張 |
| FR-022 | 評価軸生成仕様(10) | |
| FR-LOG-001 | ログメタ(11.11), スコアリング(12) | 新規 |
| FR-ALG-001 | 動的閾値(11.5), スコアリング(12) | 新規 |

## 21. 付録
### 21.1 プリセットタイプ一覧
| Name | 軸極性例 | 説明(例) |
|------|----------|----------|
| Explorer | Exploration High / Convergence Low | 新奇追求と拡散的思考 |
| Planner | Convergence High / Exploration Low | 計画重視で秩序志向 |
| Challenger | Risk High / Stability Low | 変化を好み挑戦的 |
| Supporter | Harmony High / Dominance Low | 協調性と調整力 |
| Analyzer | Analysis High / Impulse Low | 論理分析傾向 |
| Improviser | Impulse High / Structure Low | 即興的で柔軟 |

### 21.2 失敗時固定シナリオ占位（例）
| Scene | Narrative (短文) | Choices (例) |
|-------|-----------------|--------------|
| 1 | 新規プロジェクト開始 | 迅速に着手 / 情報収集 / 他者相談 / 様子見 |
| 2 | 進行停滞 | 代替案模索 / リスク分析 / メンバー鼓舞 / スコープ縮小 |
| 3 | 仕様変更 | 即時適応 / 影響整理 / 拒否交渉 / 追加時間要求 |
| 4 | デッドライン逼迫 | 集中作業 / 優先再編 / 外部支援 / 妥協提案 |

### 21.3 タイプ命名ガイド
- 英単語 1〜2 語（例: Bold Strategist → 2 語）
- ネガティブ含意回避
- 重複チェック: 大文字小文字無視 (case-insensitive set)
- 14 文字超過禁止（スペース除く）
- 衝突時: variant接尾辞（例: ExplorerX）避け、再生成推奨

---
(End of Document)
