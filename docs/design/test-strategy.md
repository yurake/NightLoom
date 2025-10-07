# テスト戦略

## 概要
バックエンド・フロントエンドの検証ケース定義と CI 統合の詳細設計。

関連 Issue: #9

## テスト階層

```
┌─────────────────────────────────┐
│   E2E テスト (Playwright)        │ ← フルユーザーフロー
├─────────────────────────────────┤
│   統合テスト (pytest/Jest)       │ ← API/コンポーネント統合
├─────────────────────────────────┤
│   ユニットテスト (pytest/Jest)   │ ← 関数・クラス単位
└─────────────────────────────────┘
```

## バックエンドテスト (pytest)

### ユニットテスト

#### セッション開始 API
```python
import pytest
from app.services.session import SessionService

def test_start_session_generates_uuid():
    """セッション ID が UUID 形式で生成される"""
    service = SessionService()
    session = service.start_session()
    assert len(session.id) == 36  # UUID format

def test_start_session_generates_initial_character():
    """50音から1文字が選択される"""
    service = SessionService()
    session = service.start_session()
    assert len(session.initial_character) == 1

def test_start_session_generates_keyword_candidates():
    """単語候補が4件生成される"""
    service = SessionService()
    session = service.start_session()
    assert len(session.keyword_candidates) == 4

def test_start_session_generates_axes():
    """評価軸が2〜6個生成される"""
    service = SessionService()
    session = service.start_session()
    assert 2 <= len(session.axes) <= 6
```

#### キーワード確定 API
```python
def test_confirm_keyword_updates_state():
    """キーワード確定でセッション状態が PLAY になる"""
    service = SessionService()
    session = service.start_session()
    service.confirm_keyword(session.id, "アート")
    updated_session = service.get_session(session.id)
    assert updated_session.state == SessionState.PLAY

def test_confirm_keyword_invalid_session():
    """存在しないセッション ID でエラー"""
    service = SessionService()
    with pytest.raises(SessionNotFoundError):
        service.confirm_keyword("invalid-id", "アート")
```

#### スコアリングロジック
```python
from app.services.scoring import ScoringService

def test_accumulate_score():
    """重みベクトルが正しく累積される"""
    scoring = ScoringService()
    weights = [
        {"axis_1": 0.5, "axis_2": 0.3},
        {"axis_1": 0.3, "axis_2": -0.2}
    ]
    result = scoring.accumulate_scores(weights)
    assert result["axis_1"] == 0.8
    assert result["axis_2"] == 0.1

def test_normalize_scores():
    """正規化が 0〜100 の範囲内"""
    scoring = ScoringService()
    raw_scores = {"axis_1": 2.5, "axis_2": -1.0}
    normalized = scoring.normalize(raw_scores)
    assert 0 <= normalized["axis_1"] <= 100
    assert 0 <= normalized["axis_2"] <= 100

def test_normalize_all_equal():
    """全軸同値時に 50 になる"""
    scoring = ScoringService()
    raw_scores = {"axis_1": 0.0, "axis_2": 0.0}
    normalized = scoring.normalize(raw_scores)
    assert normalized["axis_1"] == 50.0
    assert normalized["axis_2"] == 50.0
```

#### タイプ生成ロジック
```python
from app.services.typing import TypingService

def test_select_dominant_axes():
    """主軸が正しく選定される"""
    typing = TypingService()
    scores = {"axis_1": 75, "axis_2": 45, "axis_3": 50}
    dominant = typing.select_dominant_axes(scores, count=2)
    assert "axis_1" in dominant
    assert len(dominant) == 2

def test_validate_type_name():
    """タイプ名命名規約チェック"""
    typing = TypingService()
    assert typing.validate_type_name("Logical", []) == True
    assert typing.validate_type_name("Logical Thinker", []) == True
    assert typing.validate_type_name("Too Many Words Here", []) == False
    assert typing.validate_type_name("TooLongNameExceeds14", []) == False
```

#### LLM クライアント (モック)
```python
from unittest.mock import AsyncMock
from app.clients.llm import LLMClient, LLMRequest

@pytest.mark.asyncio
async def test_llm_generate_success():
    """LLM 呼び出しが成功する"""
    mock_client = AsyncMock(spec=LLMClient)
    mock_client.generate.return_value = LLMResponse(
        content='{"axes": [...]}',
        provider=LLMProvider.OPENAI,
        latency_ms=500,
        tokens_used=100
    )

    request = LLMRequest(prompt="test", model="gpt-4")
    response = await mock_client.generate(request)
    assert response.latency_ms == 500
```

#### フェイルオーバーロジック
```python
@pytest.mark.asyncio
async def test_failover_on_timeout():
    """タイムアウト時に1回リトライされる"""
    mock_client = AsyncMock(spec=LLMClient)
    mock_client.generate.side_effect = [
        TimeoutError(),
        LLMResponse(content='{"axes": [...]}', ...)
    ]

    service = LLMService(mock_client)
    axes, error = await service.generate_axes("あ")
    assert error is None
    assert len(axes) == 2

@pytest.mark.asyncio
async def test_failover_uses_fallback():
    """再試行失敗時にフォールバックが使用される"""
    mock_client = AsyncMock(spec=LLMClient)
    mock_client.generate.side_effect = TimeoutError()

    service = LLMService(mock_client)
    axes, error = await service.generate_axes("あ")
    assert error == "FALLBACK_USED"
    assert len(axes) == 2  # DEFAULT_AXES
```

### 統合テスト

#### API エンドツーエンド
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_session_flow():
    """セッション開始から結果取得まで"""
    # セッション開始
    response = client.post("/api/sessions/start")
    assert response.status_code == 200
    data = response.json()
    session_id = data["sessionId"]

    # キーワード確定
    response = client.post(
        f"/api/sessions/{session_id}/keyword",
        json={"keyword": "アート"}
    )
    assert response.status_code == 200

    # シーン1〜4を取得・選択
    for scene_num in range(1, 5):
        response = client.get(f"/api/sessions/{session_id}/scenes/{scene_num}")
        assert response.status_code == 200
        scene = response.json()

        response = client.post(
            f"/api/sessions/{session_id}/scenes/{scene_num}/choice",
            json={"choiceId": scene["choices"][0]["id"]}
        )
        assert response.status_code == 200

    # 結果取得
    response = client.get(f"/api/sessions/{session_id}/result")
    assert response.status_code == 200
    result = response.json()
    assert "type" in result
    assert "axes" in result
```

## フロントエンドテスト (Jest)

### ユニットテスト

#### Reducer テスト
```tsx
import { sessionReducer } from './sessionReducer';

test('SESSION_STARTED updates state correctly', () => {
  const initialState = { sessionId: null, ... };
  const action = {
    type: 'SESSION_STARTED',
    payload: {
      sessionId: 'test-id',
      initialCharacter: 'あ',
      keywordCandidates: ['アート']
    }
  };

  const newState = sessionReducer(initialState, action);
  expect(newState.sessionId).toBe('test-id');
  expect(newState.initialCharacter).toBe('あ');
});

test('KEYWORD_SELECTED transitions to scene 1', () => {
  const initialState = { currentScene: 0, ... };
  const action = {
    type: 'KEYWORD_SELECTED',
    payload: { keyword: 'アート' }
  };

  const newState = sessionReducer(initialState, action);
  expect(newState.currentScene).toBe(1);
  expect(newState.selectedKeyword).toBe('アート');
});
```

#### コンポーネントテスト (React Testing Library)
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { InitialPromptScreen } from './InitialPromptScreen';

test('renders keyword candidates', () => {
  const candidates = ['アート', 'あかり'];
  render(
    <InitialPromptScreen
      sessionId="test"
      initialCharacter="あ"
      keywordCandidates={candidates}
      onKeywordSelected={jest.fn()}
    />
  );

  expect(screen.getByText('アート')).toBeInTheDocument();
  expect(screen.getByText('あかり')).toBeInTheDocument();
});

test('calls onKeywordSelected when button clicked', () => {
  const onSelect = jest.fn();
  render(
    <InitialPromptScreen
      sessionId="test"
      initialCharacter="あ"
      keywordCandidates={['アート']}
      onKeywordSelected={onSelect}
    />
  );

  fireEvent.click(screen.getByText('アート'));
  expect(onSelect).toHaveBeenCalledWith('アート');
});
```

#### API クライアントテスト
```tsx
import { SessionApiClient } from './SessionApiClient';

global.fetch = jest.fn();

test('startSession calls correct endpoint', async () => {
  (fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => ({ sessionId: 'test-id' })
  });

  const client = new SessionApiClient('http://localhost');
  const result = await client.startSession();

  expect(fetch).toHaveBeenCalledWith(
    'http://localhost/api/sessions/start',
    expect.objectContaining({ method: 'POST' })
  );
  expect(result.sessionId).toBe('test-id');
});
```

## E2E テスト (Playwright)

### フルユーザーフロー
```typescript
import { test, expect } from '@playwright/test';

test('complete session flow', async ({ page }) => {
  // アクセス
  await page.goto('http://localhost:3000');

  // 初期単語選択
  await expect(page.getByText(/で始まる単語を選んでください/)).toBeVisible();
  await page.getByRole('button', { name: /アート|あかり/ }).first().click();

  // シーン1
  await expect(page.getByText('Scene 1 / 4')).toBeVisible();
  await page.getByRole('button').first().click();

  // シーン2
  await expect(page.getByText('Scene 2 / 4')).toBeVisible();
  await page.getByRole('button').first().click();

  // シーン3
  await expect(page.getByText('Scene 3 / 4')).toBeVisible();
  await page.getByRole('button').first().click();

  // シーン4
  await expect(page.getByText('Scene 4 / 4')).toBeVisible();
  await page.getByRole('button').first().click();

  // 結果画面
  await expect(page.getByRole('heading', { level: 2 })).toBeVisible();
  await expect(page.getByText(/評価軸スコア/)).toBeVisible();
});

test('mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 640 });
  await page.goto('http://localhost:3000');

  // モバイル幅で表示が崩れないことを確認
  await expect(page.getByRole('button').first()).toBeVisible();
});
```

## CI 統合

### GitHub Actions ワークフロー

```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage

  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Start services
        run: |
          docker-compose up -d
          sleep 10
      - name: Run E2E tests
        run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## カバレッジ目標

| レイヤー | カバレッジ目標 |
|----------|---------------|
| バックエンド ユニット | > 80% |
| フロントエンド ユニット | > 70% |
| E2E | 主要フロー 100% |

## テスト実行コマンド

### ローカル実行
```bash
# バックエンド
cd backend
pytest

# フロントエンド
cd frontend
npm test

# E2E
npx playwright test
```

### カバレッジ付き実行
```bash
# バックエンド
cd backend
pytest --cov=app --cov-report=html

# フロントエンド
cd frontend
npm test -- --coverage
```

## 実装優先度
1. バックエンド ユニットテスト (スコアリング、タイプ生成)
2. API 統合テスト
3. フロントエンド コンポーネントテスト
4. E2E フルフロー
5. CI 統合

## 参考
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- 既存 CI 設定
