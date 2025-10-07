# セッションブートストラップ API 設計

## 概要
セッション開始時の評価軸生成と初期単語候補提示機能の詳細設計。

関連 Issue: #2

## エンドポイント

### POST `/api/sessions/start`

セッションを開始し、評価軸と初期単語候補を返す。

#### リクエスト
```json
{}
```

#### レスポンス
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "initialCharacter": "あ",
  "keywordCandidates": ["アート", "あかり", "あおぞら", "あたたかい"],
  "axes": [
    {
      "id": "axis_1",
      "name": "論理性",
      "description": "論理的思考と感情的判断のバランス",
      "direction": "論理的 ⟷ 感情的"
    },
    {
      "id": "axis_2",
      "name": "社交性",
      "description": "集団行動と個人行動の指向性",
      "direction": "社交的 ⟷ 内省的"
    }
  ]
}
```

#### 処理フロー

1. **セッション ID 生成**
   - UUIDv4 を生成
   - セッション状態を `STATE_INIT` で初期化

2. **50音ランダム抽出**
   - ひらがな50音表から1文字をランダム選択
   - 選択確率は均等分布

3. **評価軸生成**
   - LLM に評価軸生成を依頼
   - 軸数: 2〜6 の範囲
   - 軸範囲外の場合は1回リトライ
   - 再失敗時は既定2軸にフォールバック

4. **初期単語候補生成**
   - 抽出した文字で始まる単語候補4件を生成
   - 評価軸との関連性を考慮

5. **セッション状態保存**
   - メモリ内にセッション情報を保存
   - タイムアウト: 30分

## データ構造

### Session
```python
@dataclass
class Session:
    id: str
    state: SessionState
    initial_character: str
    axes: list[Axis]
    scenes: list[Scene]
    scores: dict[str, float]
    created_at: datetime
    updated_at: datetime
```

### Axis
```python
@dataclass
class Axis:
    id: str
    name: str
    description: str
    direction: str  # "極性A ⟷ 極性B"
```

### SessionState
```python
class SessionState(Enum):
    INIT = "init"
    PLAY = "play"
    RESULT = "result"
    TERMINATED = "terminated"
```

## LLM プロンプト設計

### 評価軸生成プロンプト
```
あなたは性格診断アプリの評価軸を設計する専門家です。

以下の条件で評価軸を生成してください:
- 軸数: 2〜6個
- 各軸には名称、説明、方向性（極性A ⟷ 極性B）を含める
- 初期文字「{character}」に関連する単語候補を考慮した軸を設計する

出力形式:
{
  "axes": [
    {
      "id": "axis_1",
      "name": "軸名",
      "description": "説明",
      "direction": "極性A ⟷ 極性B"
    }
  ]
}
```

### 単語候補生成プロンプト
```
以下の条件で単語候補を4つ生成してください:
- 初期文字: {character}
- 評価軸との関連性を考慮
- 単語の長さ: 2〜8文字

出力形式:
{
  "candidates": ["単語1", "単語2", "単語3", "単語4"]
}
```

## エラーハンドリング

### エラーコード
| コード | 説明 | HTTP ステータス |
|--------|------|-----------------|
| `AXIS_GEN_FAILED` | 評価軸生成失敗（再試行後） | 500 |
| `KEYWORD_GEN_FAILED` | 単語候補生成失敗 | 500 |
| `SESSION_CREATE_FAILED` | セッション作成失敗 | 500 |
| `INVALID_AXIS_COUNT` | 軸数範囲外（2〜6） | 500 |

### フォールバック

#### 評価軸フォールバック
```python
DEFAULT_AXES = [
    Axis(
        id="axis_default_1",
        name="論理性",
        description="論理的思考と感情的判断",
        direction="論理的 ⟷ 感情的"
    ),
    Axis(
        id="axis_default_2",
        name="社交性",
        description="集団行動と個人行動",
        direction="社交的 ⟷ 内省的"
    )
]
```

## 非機能要件

### パフォーマンス
- p95 レイテンシ: ≤ 1.0s (LLM 呼び出し含む)
- タイムアウト: 5s

### 信頼性
- LLM 失敗時の再試行: 1回
- フォールバック成功率: > 99%

### セキュリティ
- セッション ID は推測困難 (UUIDv4 128bit)
- PII 非収集

## テストケース

### 正常系
- [x] セッション ID が生成される
- [x] 50音から1文字が選択される
- [x] 評価軸が2〜6個生成される
- [x] 単語候補が4件生成される
- [x] セッション状態が `INIT` になる

### 異常系
- [x] 評価軸生成失敗時にリトライされる
- [x] 再失敗時に既定2軸にフォールバック
- [x] 軸数範囲外時にリトライされる
- [x] タイムアウト時にエラーが返る

## 実装優先度
1. セッション ID 生成・状態管理
2. 50音ランダム抽出
3. 評価軸生成（LLM モック）
4. 単語候補生成（LLM モック）
5. フォールバックロジック
6. LLM 本番連携

## 参考
- [要件定義](../requirements/overview.md) §7, §10
- [設計概要](./overview.md) §3.2
- 関連 FR: FR-001, FR-004, FR-005, FR-022
