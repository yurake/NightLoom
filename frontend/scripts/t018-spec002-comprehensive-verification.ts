
import * as fs from 'fs';
import * as path from 'path';
import { 
  parseChecklistFromMarkdown, 
  verifyImplementationStatus,
  calculateProgressMetrics,
  analyzeFileImplementation,
  ChecklistData,
  ChecklistItem,
  FileAnalysis
} from './utils/checklist-verification';

interface ComponentVerificationResult {
  component: string;
  filePath: string;
  analysis: FileAnalysis;
  status: 'implemented' | 'partial' | 'not-implemented';
  testFilePath?: string;
  testAnalysis?: FileAnalysis;
  details: string[];
}

interface ComprehensiveVerificationReport {
  checklistData: ChecklistData;
  componentVerifications: ComponentVerificationResult[];
  testResults: {
    unitTests: boolean;
    e2eTests: boolean;
    details: string[];
  };
  qualityAssessment: {
    codeQuality: 'excellent' | 'good' | 'needs-improvement' | 'poor';
    testCoverage: 'high' | 'medium' | 'low';
    implementation: 'complete' | 'partial' | 'incomplete';
    recommendations: string[];
  };
  summary: {
    totalItems: number;
    completedItems: number;
    progressPercentage: number;
    implementationRate: number;
    readinessLevel: 'production-ready' | 'near-complete' | 'in-development' | 'early-stage';
  };
}

/**
 * spec 002の包括的検証を実行
 */
export async function runSpec002ComprehensiveVerification(): Promise<ComprehensiveVerificationReport> {
  console.log('🔍 spec 002 実装状況の包括的検証を開始します...\n');

  // 1. チェックリストデータの解析
  const checklistPath = path.join(process.cwd(), '..', 'specs', '002-nightloom-kekka-gamen-hyoji', 'checklists', 'implementation-progress.md');
  const checklistContent = fs.readFileSync(checklistPath, 'utf-8');
  const checklistData = parseChecklistFromMarkdown(checklistContent);
  
  console.log(`📊 チェックリスト解析完了: ${checklistData.totalItems}項目中${checklistData.completedItems}項目完了 (${checklistData.progressPercentage}%)\n`);

  // 2. 重要コンポーネントの実装状況検証
  const componentsToVerify = [
    {
      component: 'TypeCard',
      filePath: 'frontend/app/(play)/components/TypeCard.tsx',
      testFilePath: 'frontend/tests/components/result/TypeCard.test.tsx'
    },
    {
      component: 'AxesScores',
      filePath: 'frontend/app/(play)/components/AxesScores.tsx',
      testFilePath: 'frontend/tests/components/result/AxesScores.test.tsx'
    },
    {
      component: 'AxisScoreItem',
      filePath: 'frontend/app/(play)/components/AxisScoreItem.tsx',
      testFilePath: 'frontend/tests/components/result/AxisScoreItem.test.tsx'
    },
    {
      component: 'ResultScreen',
      filePath: 'frontend/app/(play)/components/ResultScreen.tsx',
      testFilePath: 'frontend/tests/components/result/ResultScreen.test.tsx'
    },
    {
      component: 'ActionButtons',
      filePath: 'frontend/app/(play)/components/ActionButtons.tsx',
      testFilePath: 'frontend/tests/components/result/ActionButtons.test.tsx'
    }
  ];

  const componentVerifications: ComponentVerificationResult[] = [];

  for (const comp of componentsToVerify) {
    console.log(`🔍 ${comp.component} コンポーネントを検証中...`);
    
    const analysis = await analyzeFileImplementation(comp.filePath);
    const status = await verifyImplementationStatus({
      id: `comp-${comp.component.toLowerCase()}`,
      task: `${comp.component} コンポーネント実装`,
      completed: false,
      filePath: comp.filePath
    });

    const details: string[] = [];
    details.push(`存在: ${analysis.exists ? '✅' : '❌'}`);
    details.push(`実装: ${analysis.hasImplementation ? '✅' : '❌'}`);
    details.push(`型定義: ${analysis.hasTypes ? '✅' : '❌'}`);
    details.push(`品質: ${analysis.codeQuality}`);

    let testAnalysis: FileAnalysis | undefined;
    if (comp.testFilePath) {
      testAnalysis = await analyzeFileImplementation(comp.testFilePath);
      details.push(`テスト存在: ${testAnalysis.exists ? '✅' : '❌'}`);
      details.push(`テストケース: ${testAnalysis.hasTests ? '✅' : '❌'}`);
    }

    componentVerifications.push({
      component: comp.component,
      filePath: comp.filePath,
      analysis,
      status,
      testFilePath: comp.testFilePath,
      testAnalysis,
      details
    });

    console.log(`  - ステータス: ${status}`);
    console.log(`  - 詳細: ${details.join(', ')}\n`);
  }

  // 3. テスト実行状況の確認
  console.log('🧪 テスト実行状況を確認中...');
  
  const unitTestsExist = componentVerifications.every(cv => cv.testAnalysis?.exists);
  const e2eTestPath = 'frontend/e2e/results.spec.ts';
  const e2eTestAnalysis = await analyzeFileImplementation(e2eTestPath);
  
  const testResults = {
    unitTests: unitTestsExist && componentVerifications.every(cv => cv.testAnalysis?.hasTests),
    e2eTests: e2eTestAnalysis.exists && e2eTestAnalysis.hasTests,
    details: [
      `ユニットテスト: ${unitTestsExist ? '✅' : '❌'}`,
      `E2Eテスト: ${e2eTestAnalysis.exists ? '✅' : '❌'}`,
      `テストケース実装: ${componentVerifications.filter(cv => cv.testAnalysis?.hasTests).length}/${componentVerifications.length}`
    ]
  };

  // 4. 品質評価
  console.log('\n📊 品質評価を実施中...');
  
  const implementedComponents = componentVerifications.filter(cv => cv.status === 'implemented').length;
  const partialComponents = componentVerifications.filter(cv => cv.status === 'partial').length;
  const notImplementedComponents = componentVerifications.filter(cv => cv.status === 'not-implemented').length;
  
  const implementationRate = Math.round((implementedComponents / componentVerifications.length) * 100);
  
  let codeQuality: 'excellent' | 'good' | 'needs-improvement' | 'poor';
  if (implementedComponents >= 4 && componentVerifications.every(cv => cv.analysis.codeQuality !== 'poor')) {
    codeQuality = 'excellent';
  } else if (implementedComponents >= 3) {
    codeQuality = 'good';
  } else if (implementedComponents >= 2) {
    codeQuality = 'needs-improvement';
  } else {
    codeQuality = 'poor';
  }

  let testCoverage: 'high' | 'medium' | 'low';
  const testCoverageRate = componentVerifications.filter(cv => cv.testAnalysis?.hasTests).length / componentVerifications.length;
  if (testCoverageRate >= 0.8) {
    testCoverage = 'high';
  } else if (testCoverageRate >= 0.5) {
    testCoverage = 'medium';
  } else {
    testCoverage = 'low';
  }

  let implementation: 'complete' | 'partial' | 'incomplete';
  if (implementationRate >= 90) {
    implementation = 'complete';
  } else if (implementationRate >= 50) {
    implementation = 'partial';
  } else {
    implementation = 'incomplete';
  }

  const recommendations: string[] = [];
  if (notImplementedComponents > 0) {
    recommendations.push(`${notImplementedComponents}個のコンポーネントが未実装です`);
  }
  if (testCoverage === 'low') {
    recommendations.push('テストカバレッジの向上が必要です');
  }
  if (componentVerifications.some(cv => cv.analysis.codeQuality === 'poor')) {
    recommendations.push('品質の低いコンポーネントのリファクタリングを推奨します');
  }
  if (!testResults.e2eTests) {
    recommendations.push('E2Eテストの実装が必要です');
  }

  let readinessLevel: 'production-ready' | 'near-complete' | 'in-development' | 'early-stage';
  if (implementationRate >= 95 && testCoverage === 'high' && testResults.e2eTests) {
    readinessLevel = 'production-ready';
  } else if (implementationRate >= 80 && testCoverage !== 'low') {
    readinessLevel = 'near-complete';
  } else if (implementationRate >= 50) {
    readinessLevel = 'in-development';
  } else {
    readinessLevel = 'early-stage';
  }

  const qualityAssessment = {
    codeQuality,
    testCoverage,
    implementation,
    recommendations
  };

  const summary = {
    totalItems: checklistData.totalItems,
    completedItems: checklistData.completedItems,
    progressPercentage: checklistData.progressPercentage,
    implementationRate,
    readinessLevel
  };

  console.log('\n✅ 検証完了');

  return {
    checklistData,
    componentVerifications,
    testResults,
    qualityAssessment,
    summary
  };
}

/**
 * 検証結果レポートを生成
 */
export function generateVerificationReport(report: ComprehensiveVerificationReport): string {
  const timestamp = new Date().toISOString();
  
  let markdown = `# spec 002 実装状況包括的検証レポート

**生成日時**: ${timestamp}  
**検証対象**: NightLoom結果画面表示機能  
**spec**: 002-nightloom-kekka-gamen-hyoji

## 📊 検証サマリー

### 全体進捗
- **総項目数**: ${report.summary.totalItems}
- **完了項目数**: ${report.summary.completedItems}
- **進捗率**: ${report.summary.progressPercentage}%
- **実装率**: ${report.summary.implementationRate}%
- **準備レベル**: ${report.summary.readinessLevel}

### 品質評価
- **コード品質**: ${report.qualityAssessment.codeQuality}
- **テストカバレッジ**: ${report.qualityAssessment.testCoverage}
- **実装状況**: ${report.qualityAssessment.implementation}

## 🔍 コンポーネント別検証結果

`;

  // コンポーネント別の詳細
  report.componentVerifications.forEach(cv => {
    const statusIcon = cv.status === 'implemented' ? '✅' : cv.status === 'partial' ? '⚠️' : '❌';
    
    markdown += `### ${statusIcon} ${cv.component} コンポーネント

**ファイルパス**: [\`${cv.filePath}\`](${cv.filePath})  
**実装ステータス**: ${cv.status}  
**品質レベル**: ${cv.analysis.codeQuality}

**検証結果**:
`;
    cv.details.forEach(detail => {
      markdown += `- ${detail}\n`;
    });
    
    if (cv.testFilePath && cv.testAnalysis) {
      markdown += `\n**テストファイル**: [\`${cv.testFilePath}\`](${cv.testFilePath})  \n`;
      markdown += `**テスト実装**: ${cv.testAnalysis.hasTests ? '✅' : '❌'}\n`;
    }
    
    markdown += '\n';
  });

  // テスト結果
  markdown += `## 🧪 テスト実行結果

`;
  report.testResults.details.forEach(detail => {
    markdown += `- ${detail}\n`;
  });

  // 推奨事項
  if (report.qualityAssessment.recommendations.length > 0) {
    markdown += `\n## 🎯 改善推奨事項

`;
    report.qualityAssessment.recommendations.forEach((rec, index) => {
      markdown += `${index + 1}. ${rec}\n`;
    });
  }

  // フェーズ別進捗
  if (report.checklistData.sections.length > 0) {
    markdown += `\n## 📈 フェーズ別進捗状況

`;
    const metrics = calculateProgressMetrics(report.checklistData.sections);
    metrics.phaseProgress.forEach(phase => {
      const statusIcon = phase.progress >= 100 ? '✅' : phase.progress >= 50 ? '🔄' : '⏳';
      markdown += `- ${statusIcon} **${phase.phase}**: ${phase.progress}%\n`;
    });
  }

  markdown += `\n## 📝 次のアクション

`;

  switch (report.summary.readinessLevel) {
    case 'production-ready':
      markdown += '🎉 実装完了！本番デプロイの準備が整っています。\n';
      break;
    case 'near-complete':
      markdown += '🔧 最終調整段階です。残りの実装とテストを完了させてください。\n';
      break;
    case 'in-development':
      markdown += '🚧 開発継続中です。重要なコンポーネントの実装を優先してください。\n';
      break;
    case 'early-stage':
      markdown += '🌱 初期段階です。基本コンポーネントの実装から始めてください。\n';
      break;
  }

  markdown += `\n---
*このレポートは [T018-spec002-comprehensive-verification.ts](frontend/scripts/t018-spec002-comprehensive-verification.ts) により自動生成されました。*
`;

  return markdown;
}
// スクリプト直接実行時の処理
if (require.main === module) {
  runSpec002ComprehensiveVerification()
    .then(report => {
      const reportMarkdown = generateVerificationReport(report);
      
      // レポートファイルに保存
      const reportPath = path.join(process.cwd(), `T018-SPEC002-VERIFICATION-REPORT-${new Date().toISOString().split('T')[0]}.md`);
      fs.writeFileSync(reportPath, reportMarkdown, 'utf-8');
      
      console.log(`\n📄 検証レポートを生成しました: ${reportPath}`);
      console.log('\n=== 検証結果サマリー ===');
      console.log(`準備レベル: ${report.summary.readinessLevel}`);
      console.log(`実装率: ${report.summary.implementationRate}%`);
      console.log(`コード品質: ${report.qualityAssessment.codeQuality}`);
      console.log(`テストカバレッジ: ${report.qualityAssessment.testCoverage}`);
      
      if (report.qualityAssessment.recommendations.length > 0) {
        console.log('\n🎯 改善推奨事項:');
        report.qualityAssessment.recommendations.forEach((rec, index) => {
          console.log(`  ${index + 1}. ${rec}`);
        });
      }
    })
    .catch(error => {
      console.error('❌ 検証実行中にエラーが発生しました:', error);
      process.exit(1);
    });
}
      