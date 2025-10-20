/**
 * T004 ベースライン測定実行スクリプト
 * 
 * コマンドライン経由でベースライン測定を実行するためのNode.jsスクリプト
 * npm run baseline-test で実行可能
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🎯 [T004] ベースライン測定準備開始');

// 測定結果保存ディレクトリの作成
const resultsDir = path.join(__dirname, '..', 'baseline-results');
if (!fs.existsSync(resultsDir)) {
  fs.mkdirSync(resultsDir);
  console.log('📁 結果保存ディレクトリを作成:', resultsDir);
}

// 測定実行時刻
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const reportFile = path.join(resultsDir, `baseline-report-${timestamp}.md`);

// 測定レポートのテンプレート作成
const reportContent = `# T004 ベースライン測定レポート

**測定実行日時:** ${new Date().toLocaleString('ja-JP')}  
**タスク:** ResultScreenコンポーネント動作時間測定  
**目的:** T015でのActionButtonsコンポーネント分離前後の性能比較用基準値確立

## 測定内容

- **対象コンポーネント:** ResultScreenWithMetrics.tsx
- **測定項目:**
  - コンポーネントマウント時間
  - データフェッチ時間
  - TypeCard計算時間
  - AxesScores計算時間
  - 総レンダリング時間

## 測定方法

1. 開発サーバーを起動: \`pnpm dev\`
2. テストページにアクセス: http://localhost:3000/test-baseline
3. 測定実行（5回平均）
4. 結果をlocalStorage・CSVに保存

## 基準値設定

測定平均値 + 5% = T015での許容閾値

## 使用技術

- **パフォーマンス測定:** Web Performance API + カスタム測定ツール
- **測定精度:** ±5%以内の要件
- **測定環境:** Next.js 14開発環境

## 実行手順

\`\`\`bash
# 1. 開発サーバー起動
pnpm --filter nightloom-frontend dev

# 2. 別ターミナルでベースライン測定実行
pnpm --filter nightloom-frontend baseline-test

# 3. ブラウザでテストページ確認
open http://localhost:3000/test-baseline
\`\`\`

## 測定結果

測定結果はコンソールログ、localStorage(\`t004_baseline_complete\`)、
およびCSVファイルで確認可能。

## 後続タスクへの引き継ぎ

- **T015:** ActionButtonsコンポーネント分離後の性能比較
- **比較基準:** 本測定で確立した基準値±5%以内
- **データ保存:** localStorage.t004_baseline_complete

---

**注意:** この測定はActionButtonsコンポーネント分離前の
現在のResultScreenコンポーネントの性能基準値を確立するものです。
`;

fs.writeFileSync(reportFile, reportContent);
console.log('📊 測定レポートを作成:', reportFile);

console.log('\n🎯 [T004] 手動測定手順:');
console.log('1. pnpm --filter nightloom-frontend dev (開発サーバー起動)');
console.log('2. http://localhost:3000/test-baseline にアクセス');
console.log('3. 「標準測定（5回）」ボタンをクリック');
console.log('4. コンソールログとCSVダウンロードで結果確認');
console.log('5. localStorage.t004_baseline_complete で完全データ確認\n');

console.log('✅ T004 ベースライン測定準備完了');
console.log(`📂 結果保存先: ${resultsDir}`);
console.log(`📋 レポート: ${reportFile}`);
