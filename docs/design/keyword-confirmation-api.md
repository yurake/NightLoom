# キーワード確定・シーン取得 API 設計

## 概要
ユーザーが選択したキーワードを確定し、シーンのシナリオと選択肢を取得する機能の詳細設計。

関連 Issue: #3

## エンドポイント

### POST `/api/sessions/{sessionId}/keyword`

初期単語を確定し、セッションを PLAY 状態に遷移させる。

#### リクエスト
```json
{
  "keyword": "アート",
  "customInput": false
}
```

#### レスポンス
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "keyword": "アート",
  "state": "play"
}
```

### GET `/api/sessions/{sessionId}/scenes/{sceneNumber}`

指定シーン番号のシナリオと選択肢を取得する。

#### パラメータ
- `sessionId`: セッション ID (UUID)
- `sceneNumber`: シーン番号 (1〜4)

#### レスポンス
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "sceneNumber": 1,
  "scenario": "あなたはアートギャラリーの前に立っています。今日は特別な展示会が開催されており、入場は無料です。しかし、あなたには他にも予定があります。",
  "choices": [
    {
      "id": "choice_1_1",
      "text": "展示会に入る",
      "weights": {
        "axis_1": 0.6,
        "axis_2": 0.3
      }
    },
    {
      "id": "choice_1_2",
      "text": "予定を優先する",
      "weights": {
        "axis_1": 0.8,
        "axis_2": -0.2
      }
    },
    {
      "id": "choice_1_3",
      "text": "友人を誘って後で来る",
      "weights": {
        "axis_1": -0.3,
        "axis_2": 0.7
      }
    },
    {
      "id": "choice_1_4",
      "text": "パンフレットだけもらう",
      "weights": {
        "axis_1": 0.4,
        "axis_2": -0.5
      }
    }
  ]
}
```

### POST `/api/sessions/{sessionId}/scenes/{sceneNumber}/choice`

シーンの選択肢を記録し、スコアを加算する。

#### リクエスト
```json
{
  "choiceId": "choice_1_1"
}
```

#### レスポンス
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "sceneNumber": 1,
  "choiceId": "choice_1_1",
  "nextScene": 2
}
```

## 処理フロー

### キーワード確定
1. セッション存在確認
2. セッション状態が `INIT` であることを確認
3. キーワードをセッションに記録
4. 初期スコア補正値を計算（キーワードと評価軸の関連度）
5. セッション状態を `PLAY` に変更

### シーン取得
1. セッション存在確認
2. セッション状態が `PLAY` であることを確認
3. シーン番号の妥当性確認 (1〜4)
4. 既に取得済みの場合はキャッシュから返却
5. 未取得の場合は LLM でシナリオ生成
6. 選択肢ごとの重みベクトルを生成
7. シーン情報をキャッシュ

### 選択記録
1. セッション存在確認
2. シーン番号の妥当性確認
3. 選択肢 ID の妥当性確認
4. 重みベクトルを内部スコアに加算
5. 次シーン番号を返却（4シーン目の場合は null）

## データ構造

### Scene
```python
@dataclass
class Scene:
    number: int
    scenario: str
    choices: list[Choice]
    generated_at: datetime
```

### Choice
```python
@dataclass
class Choice:
    id: str
    text: str
    weights: dict[str, float]  # axis_id -> weight
```

### ScoreState
```python
@dataclass
class ScoreState:
    axis_scores: dict[str, float]  # axis_id -> cumulative score
    keyword_modifier: dict[str, float]  # axis_id -> modifier
    selected_choices: list[str]  # choice_ids
```

## LLM プロンプト設計

### シナリオ生成プロンプト
```
あなたは性格診断アプリのシナリオライターです。

以下の条件でシーン{scene_number}のシナリオと選択肢を生成してください:
- キーワード: {keyword}
- 評価軸: {axes}
- シナリオは2〜3文程度の短尺
- 選択肢は4つ
- 各選択肢は評価軸に対する重みベクトルを持つ（-1.0〜1.0）

前のシーンの選択: {previous_choice}

出力形式:
{
  "scenario": "シナリオ文",
  "choices": [
    {
      "id": "choice_{scene_number}_1",
      "text": "選択肢テキスト",
      "weights": {
        "axis_1": 0.6,
        "axis_2": 0.3
      }
    }
  ]
}
```

### キーワード初期スコア計算プロンプト
```
キーワード「{keyword}」が各評価軸に与える影響度を算出してください（-1.0〜1.0）:
- 評価軸: {axes}

出力形式:
{
  "modifiers": {
    "axis_1": 0.2,
    "axis_2": -0.1
  }
}
```

## 状態遷移

```
INIT → (keyword確定) → PLAY → (4シーン選択完了) → RESULT
```

### 状態遷移条件
| 現在状態 | イベント | 次状態 | 条件 |
|----------|----------|--------|------|
| INIT | keyword確定 | PLAY | キーワードが有効 |
| PLAY | 選択記録 | PLAY | シーン1〜3 |
| PLAY | 選択記録 | RESULT | シーン4 |

## エラーハンドリング

### エラーコード
| コード | 説明 | HTTP ステータス |
|--------|------|-----------------|
| `SESSION_NOT_FOUND` | セッション ID が無効 | 404 |
| `INVALID_STATE` | セッション状態が不正 | 400 |
| `INVALID_SCENE_NUMBER` | シーン番号範囲外 (1〜4以外) | 400 |
| `INVALID_CHOICE_ID` | 選択肢 ID が不正 | 400 |
| `SCENARIO_GEN_FAILED` | シナリオ生成失敗 | 500 |
| `ALREADY_COMPLETED` | 既に結果取得済み | 400 |

### バリデーション
- セッション ID: UUID 形式
- シーン番号: 1〜4
- 選択肢 ID: `choice_{scene}_{n}` 形式
- キーワード: 1〜20文字

## 非機能要件

### パフォーマンス
- p95 シーン取得: ≤ 800ms
- p95 選択記録: ≤ 100ms

### 信頼性
- シナリオ生成失敗時: 固定シナリオへフォールバック
- 重みベクトル異常時: 均等配分にフォールバック

## テストケース

### 正常系
- [x] キーワード確定でセッション状態が PLAY になる
- [x] シーン1〜4が順番に取得できる
- [x] 選択肢を記録するとスコアが加算される
- [x] シーン4の選択後に次シーンが null になる

### 異常系
- [x] 存在しないセッション ID でエラー
- [x] INIT 状態でシーン取得を試みるとエラー
- [x] RESULT 状態でシーン取得を試みるとエラー
- [x] シーン番号範囲外でエラー
- [x] 不正な選択肢 ID でエラー
- [x] シナリオ生成失敗時にフォールバック

## 実装優先度
1. キーワード確定エンドポイント
2. シーン取得エンドポイント（モック）
3. 選択記録エンドポイント
4. スコア加算ロジック
5. 状態遷移管理
6. LLM シナリオ生成統合
7. フォールバック実装

## 参考
- [要件定義](../requirements/overview.md) §7, §9, §13
- [設計概要](./overview.md) §2, §3.1
- 関連 FR: FR-002, FR-003, FR-014, FR-020
