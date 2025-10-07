# スコアリング・タイプ生成サービス設計

## 概要
選択パターンから評価軸スコアを算出し、タイプ分類を動的生成する機能の詳細設計。

関連 Issue: #4

## エンドポイント

### GET `/api/sessions/{sessionId}/result`

最終結果（正規化スコア + タイプ判定）を取得する。

#### レスポンス
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "keyword": "アート",
  "axes": [
    {
      "id": "axis_1",
      "name": "論理性",
      "description": "論理的思考と感情的判断",
      "direction": "論理的 ⟷ 感情的",
      "score": 65.5,
      "rawScore": 2.4
    },
    {
      "id": "axis_2",
      "name": "社交性",
      "description": "集団行動と個人行動",
      "direction": "社交的 ⟷ 内省的",
      "score": 42.3,
      "rawScore": -0.8
    }
  ],
  "type": {
    "name": "Logical Thinker",
    "description": "論理的思考を重視し、個人での内省を好む傾向があります。",
    "dominantAxes": ["axis_1", "axis_2"],
    "polarity": "Hi-Lo"
  },
  "completedAt": "2025-10-07T18:20:00Z"
}
```

## 処理フロー

### 結果生成
1. セッション存在確認
2. セッション状態が `PLAY` かつ4シーン完了を確認
3. スコア正規化処理
4. 主軸選定
5. タイプ分類生成
6. セッション状態を `RESULT` に変更
7. 結果を返却

## スコアリングロジック

### 1. 重みベクトル累積加算

```python
def accumulate_score(session: Session) -> dict[str, float]:
    """選択肢の重みベクトルを累積加算"""
    raw_scores = {axis.id: 0.0 for axis in session.axes}

    # キーワード初期修正値を加算
    for axis_id, modifier in session.keyword_modifier.items():
        raw_scores[axis_id] += modifier

    # 各選択の重みを加算
    for scene in session.scenes:
        selected_choice = get_selected_choice(scene)
        for axis_id, weight in selected_choice.weights.items():
            raw_scores[axis_id] += weight

    return raw_scores
```

### 2. 正規化処理 (0〜100)

```python
def normalize_scores(raw_scores: dict[str, float],
                     axes: list[Axis]) -> dict[str, float]:
    """スコアを 0〜100 に線形正規化"""
    # 理論値範囲を計算
    # キーワード修正: -1.0 〜 1.0
    # 4シーン × 重み範囲: -4.0 〜 4.0
    # 合計範囲: -5.0 〜 5.0
    min_raw = -5.0
    max_raw = 5.0

    normalized = {}
    for axis_id, raw_score in raw_scores.items():
        # 線形変換: [-5.0, 5.0] → [0, 100]
        normalized[axis_id] = (raw_score - min_raw) / (max_raw - min_raw) * 100
        normalized[axis_id] = max(0.0, min(100.0, normalized[axis_id]))

    return normalized
```

### 3. 特殊ケース処理

#### 全軸同値の場合
```python
def handle_neutral_case(scores: dict[str, float]) -> dict[str, float]:
    """全軸が同じスコアの場合は50に統一"""
    values = list(scores.values())
    if len(set(values)) == 1:
        return {axis_id: 50.0 for axis_id in scores.keys()}
    return scores
```

## タイプ分類ロジック

### 1. 主軸選定

```python
def select_dominant_axes(normalized_scores: dict[str, float],
                         count: int = 2) -> list[str]:
    """分散が最も大きい軸を主軸として選定"""
    mean_score = sum(normalized_scores.values()) / len(normalized_scores)

    # 各軸の平均からの偏差を計算
    deviations = {
        axis_id: abs(score - mean_score)
        for axis_id, score in normalized_scores.items()
    }

    # 偏差が大きい順にソート
    sorted_axes = sorted(deviations.items(),
                        key=lambda x: x[1],
                        reverse=True)

    return [axis_id for axis_id, _ in sorted_axes[:count]]
```

### 2. 極性判定

```python
def determine_polarity(score: float, threshold_high: float = 60.0,
                       threshold_low: float = 40.0) -> str:
    """スコアから極性を判定"""
    if score >= threshold_high:
        return "Hi"
    elif score <= threshold_low:
        return "Lo"
    else:
        return "Mid"
```

### 3. タイプ名生成

#### LLM プロンプト
```
以下の評価結果からタイプ名と説明を生成してください:

評価軸スコア:
{axis_scores}

主軸: {dominant_axes}
極性: {polarity_pattern}

条件:
- タイプ名: 英語1〜2語、最大14文字
- 既存タイプとの重複不可: {existing_types}
- 不適切語の使用不可
- タイプ数: 4〜6種

出力形式:
{
  "types": [
    {
      "name": "Logical Thinker",
      "description": "説明文（50文字以内）",
      "dominantAxes": ["axis_1", "axis_2"],
      "polarity": "Hi-Lo"
    }
  ]
}
```

### 4. 命名規約チェック

```python
def validate_type_name(name: str, existing_types: list[str]) -> bool:
    """タイプ名の妥当性検証"""
    # 長さチェック
    if len(name) > 14:
        return False

    # 英語のみチェック
    if not name.replace(" ", "").isalpha():
        return False

    # 単語数チェック (1〜2語)
    words = name.split()
    if len(words) > 2:
        return False

    # 重複チェック
    if name in existing_types:
        return False

    return True
```

### 5. 重複検出とリネーム

```python
def handle_duplicate_names(types: list[TypeResult],
                          retry_count: int = 1) -> list[TypeResult]:
    """重複したタイプ名をリネーム"""
    seen_names = set()
    result = []

    for type_result in types:
        if type_result.name in seen_names:
            # 1回だけ再生成を試行
            if retry_count > 0:
                new_type = regenerate_type_name(type_result)
                result.append(new_type)
            else:
                # 失敗時はサフィックス付与
                suffix = 1
                while f"{type_result.name} {suffix}" in seen_names:
                    suffix += 1
                type_result.name = f"{type_result.name} {suffix}"
                result.append(type_result)
        else:
            result.append(type_result)

        seen_names.add(result[-1].name)

    return result
```

## データ構造

### TypeResult
```python
@dataclass
class TypeResult:
    name: str
    description: str
    dominant_axes: list[str]
    polarity: str  # "Hi-Hi", "Hi-Lo", "Lo-Hi", "Lo-Lo", "Hi-Mid", etc.
```

### ScoreResult
```python
@dataclass
class ScoreResult:
    axis_id: str
    axis_name: str
    description: str
    direction: str
    score: float  # 正規化後 (0〜100)
    raw_score: float  # 正規化前
```

## エラーハンドリング

### エラーコード
| コード | 説明 | HTTP ステータス |
|--------|------|-----------------|
| `SESSION_NOT_FOUND` | セッション ID が無効 | 404 |
| `SESSION_NOT_COMPLETED` | 4シーン未完了 | 400 |
| `TYPE_GEN_FAILED` | タイプ生成失敗 | 500 |
| `INVALID_TYPE_COUNT` | タイプ数範囲外 (4〜6以外) | 500 |
| `DUPLICATE_TYPE_NAME` | 重複検出失敗 | 500 |

### フォールバック

#### プリセットタイプ (6種)
```python
PRESET_TYPES = [
    TypeResult(
        name="Balanced Mind",
        description="バランスの取れた判断を行う傾向があります。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Mid-Mid"
    ),
    TypeResult(
        name="Strategic",
        description="論理的で計画的な行動を好む傾向があります。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Hi-Lo"
    ),
    TypeResult(
        name="Empathetic",
        description="感情を重視し、他者との調和を大切にします。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Lo-Hi"
    ),
    TypeResult(
        name="Independent",
        description="独立心が強く、個人での活動を好みます。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Hi-Hi"
    ),
    TypeResult(
        name="Harmonizer",
        description="調和を重視し、柔軟な対応ができます。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Lo-Lo"
    ),
    TypeResult(
        name="Explorer",
        description="新しい経験を求め、積極的に行動します。",
        dominant_axes=["axis_1", "axis_2"],
        polarity="Mid-Hi"
    )
]
```

## 非機能要件

### パフォーマンス
- p95 結果生成: ≤ 1.2s
- スコア計算単体: < 5ms

### 信頼性
- タイプ生成失敗時: プリセットタイプを使用
- 命名規約違反時: 自動リネーム

## テストケース

### スコアリング
- [x] 重みベクトルが正しく累積される
- [x] 正規化が 0〜100 の範囲内
- [x] キーワード修正値が反映される
- [x] 全軸同値時に 50 になる

### タイプ生成
- [x] 主軸が正しく選定される
- [x] 極性判定が閾値通りに動作
- [x] タイプ名が命名規約を満たす
- [x] 重複検出が機能する
- [x] 生成失敗時にプリセットが使用される

## 実装優先度
1. スコア累積・正規化ロジック
2. 主軸選定ロジック
3. 極性判定ロジック
4. タイプ名命名規約チェック
5. LLM タイプ生成統合
6. 重複検出・リネーム
7. プリセットタイプフォールバック

## 参考
- [要件定義](../requirements/overview.md) §11, §12
- [設計概要](./overview.md) §3.3, §3.4, §5
- 関連 FR: FR-006, FR-007, FR-009, FR-010, FR-015, FR-016, FR-021, FR-023
