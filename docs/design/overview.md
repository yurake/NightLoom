# 設計概要

本ドキュメントでは MVP におけるコア機能の実装方針を整理し、要件定義書で定義された機能要件をどのような構造とアルゴリズムで実現するかを示す。

## 1. システムコンテキスト
- Web SPA クライアントが API 経由でセッション開始・選択送信・結果取得を行う。
- バックエンドはセッション状態をメモリまたは短期コンテキストに保持し、LLM へのプロンプト生成と結果整形を担う。
- LLM からの応答失敗時はプレースホルダー資材を用意し、ユーザー体験を継続させる。

## 2. セッションライフサイクルと API
### 2.1 API エンドポイント案
| フェーズ | 操作 | API 案 | メソッド | リクエスト | レスポンス(主要) |
|---------|------|--------|----------|------------|------------------|
| 開始 | セッション開始 | POST /session/start | POST | {} | {sessionId, axes[], firstScene} |
| シーン取得 | n 番目シーン | GET /session/{id}/scene/{n} | GET | path | {sceneIndex, narrative, choices[]} |
| 選択送信 | 選択反映 | POST /session/{id}/scene/{n}/choice | POST | {choiceId} | {ack:true,nextSceneIndex} |
| 結果取得 | 最終結果 | POST /session/{id}/result | POST | {} | {axesScores[], type, rawScores?} |
| 終了 | 明示破棄(任意) | DELETE /session/{id} | DELETE | path | {ack:true} |

### 2.2 ステート遷移
STATE_INIT → STATE_PLAY(n=1..4) → STATE_RESULT → STATE_TERMINATED

セッション開始時に初回シーンと評価軸メタを取得し、4 シーンの選択が完了すると結果生成フェーズへ遷移する。終了 API は任意だが、明示破棄を行うことでメモリクリーンアップを保証する。

## 3. 生成アルゴリズム設計
### 3.1 シナリオ生成
- シーン数: 4 固定。
- 各シーン選択肢: 常に 4。
- 文面特性: 高密度・短尺 (読了 5 秒以内)・過剰装飾回避。
- コンテキスト: セッション開始時に統一テーマを LLM で決定。
- 出力フォーマット例:
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
- 一意性は現段階で保証しない（重複検証は将来課題）。
- フェイルオーバー: 生成失敗時に 1 回リトライし、それでも失敗した場合は付録の固定シナリオを返却する。

### 3.2 評価軸生成
- 軸数: 2〜6（乱数または LLM 裁量）。
- 軸属性: name, description, weightNormalizationStrategy(optional), direction(HigherIsPositive or HigherIsNegative)。
- 重み付与: 選択肢単位で axis_length の配列を返却し、後段で正規化する。
- 軸名制約: 英語 Camel / Title Case 推奨、長さ上限 20 文字。
- 方向性: 結果 UI 表示やタイプ判定に用いる。
- 整合性検証: 軸数が範囲外の場合は再生成 1 回。失敗した場合は既定 2 軸 (Exploration, Convergence) を採用。

### 3.3 タイプ分類
#### 3.3.1 目的
- 動的生成された評価軸からユーザーを 4〜6 タイプに分類し、行動指向性を即座に提示する。
- 再現性より可読性・説明一貫性を優先する。

#### 3.3.2 入力と依存
| 入力 | 型 / 範囲 | 説明 |
|------|-----------|------|
| axesMeta | Array<AxisMeta> | 軸名 / 説明 / 方向性 |
| normalizedScores | number[] (0〜100) | 軸順序は axesMeta と同一 |
| axisCount | int (2〜6) | 評価軸生成ロジックで決定 |
| sessionId | string | ログ相関用 |
| generationConfig | object | 閾値・リトライ設定 |
| rng / llmClient | object | 命名・説明生成に利用 |

#### 3.3.3 制約とヒューリスティクス
| 項目 | 制約 |
|------|------|
| タイプ数 | 4〜6 |
| 主軸数 | 常に 2 (分散・レンジに基づき選定) |
| スコア域 | 各軸 0〜100 |
| 動的閾値初期値 | ±10pt |
| 動的閾値下限 | 5pt |
| 命名長 | 1〜14 文字 (スペース除く) |
| 命名語数 | 1〜2 語 |
| 再試行 | LLM 名称生成 1 回まで |
| 重複許容 | 完全一致および語幹類似を禁止 |

#### 3.3.4 生成フロー擬似コード
```
function generateTypes(axesMeta, normalizedScores, config):
    assert 2 <= len(axesMeta) <= 6
    rankedAxes = rankAxesByDispersion(normalizedScores)
    axisA, axisB = rankedAxes[0], rankedAxes[1]

    thrA = computeDynamicThreshold(normalizedScores[axisA.index], normalizedScores)
    thrB = computeDynamicThreshold(normalizedScores[axisB.index], normalizedScores)

    polarityMap = {}
    for ax in [axisA, axisB]:
        polarityMap[ax.index] = classifyHighLow(normalizedScores[ax.index], thr= ax==axisA ? thrA : thrB)

    baseCells = buildBaseCells(polarityMap)
    targetCount = decideTypeCount(baseCells, normalizedScores, config)

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
                name = fallbackPlainName(cell)
        description = buildShortDescription(cell, axesMeta, polarityMap)
        types.append(buildTypeRecord(name, cell, description))

    if not validateCompleteness(types):
        return fallbackPresetTypes()

    logGenerationMeta(types, axisA, axisB, thrA, thrB)
    return types
```

#### 3.3.5 閾値計算とタイプ数拡張
- 動的閾値: $thr = \max(5, 10 	imes \sqrt{variance / 100})$ を用いる。
- 判定式: スコア $s_i$ と平均 $\mu$ の差を閾値と比較して High/Low/Neutral を決定する。
- 両主軸が Neutral の場合は相対差 |s_a - s_b| が thr を超えた側を High とみなし二値化する。
- タイプ数は基本 4。Neutral の発生率やセル不均衡を評価し 5 または 6 へ拡張するヒューリスティクスを備える。

#### 3.3.6 命名検証
- 文字長 14 以内、英語 1〜2 語、先頭大文字。
- case-insensitive で重複禁止、語幹比較で近似語も排除。
- 禁止語リストと LLM safety 判定を併用。
- 再生成に失敗した場合は極性ベースのプレーン名へフォールバックする。

### 3.4 スコアリングと正規化
- raw スコアは選択肢ごとの重みを逐次加算する。
- 最小値・最大値を用いて 0〜100 に線形正規化し、小数第 1 位で丸める。
- 全軸同値の場合は一律 50 として Neutral 扱い。
- 平均と分散を算出し、タイプ分類ロジックの閾値計算に利用する。
- generationMeta へ variance と threshold 情報を記録する。

## 4. フォールバック設計
### 4.1 失敗検知と再試行
| 対象 | 再試行回数 | 条件 | フォールバック |
|------|------------|------|----------------|
| 軸生成 | 1 | 2〜6 範囲外 or LLM エラー | 既定2軸 (Exploration, Convergence) |
| シナリオ生成 | 1 | LLM エラー | 固定シナリオテンプレ |
| タイプ生成 | 1 | タイプ不足/命名失敗/重複 | プリセット6タイプ |
| ネット/LLM タイムアウト | 0 | timeout | 直接フォールバック |

- 各フォールバックは追加再試行を行わず、原因コード (AXIS_FALLBACK など) をログに記録する。

### 4.2 タイプ生成フォールバック詳細
1. 通常生成試行。
2. 命名や重複検証で失敗した場合は 1 回再試行。
3. 再試行でも要件を満たさない場合はプリセットタイプ 6 件を返却する。
4. failure_code=TYPE_PRESET を付与して監視対象とする。

## 5. データモデルとログ
### 5.1 JSON スキーマ例
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

### 5.2 ログとメトリクス
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
| neutral_variant_included | bool | Neutral 派生の有無 |
| failure_code | string? | TYPE_PRESET 等 |
| naming_rejection_reasons | string[] | 命名失敗理由 |

ログはダッシュボード監視とヒューリスティク調整に利用する。タイムアウトやフォールバック発生頻度が閾値を超えた場合はアラートを発砲する。

## 6. 付録
### 6.1 プリセットタイプ一覧
| Name | 軸極性例 | 説明(例) |
|------|----------|----------|
| Explorer | Exploration High / Convergence Low | 新奇追求と拡散的思考 |
| Planner | Convergence High / Exploration Low | 計画重視で秩序志向 |
| Challenger | Risk High / Stability Low | 変化を好み挑戦的 |
| Supporter | Harmony High / Dominance Low | 協調性と調整力 |
| Analyzer | Analysis High / Impulse Low | 論理分析傾向 |
| Improviser | Impulse High / Structure Low | 即興的で柔軟 |

### 6.2 固定シナリオ占位例
| Scene | Narrative (短文) | Choices (例) |
|-------|-----------------|--------------|
| 1 | 新規プロジェクト開始 | 迅速に着手 / 情報収集 / 他者相談 / 様子見 |
| 2 | 進行停滞 | 代替案模索 / リスク分析 / メンバー鼓舞 / スコープ縮小 |
| 3 | 仕様変更 | 即時適応 / 影響整理 / 拒否交渉 / 追加時間要求 |
| 4 | デッドライン逼迫 | 集中作業 / 優先再編 / 外部支援 / 妥協提案 |

### 6.3 タイプ命名ガイド
- 英単語 1〜2 語を基本とし、ネガティブな含意を避ける。
- 大文字小文字を無視した重複チェックと語幹比較を行う。
- 14 文字を超える名称は禁止。衝突時は再生成を優先し、サフィックスによる場当たり的な調整は避ける。
