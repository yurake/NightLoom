/**
 * T015 パフォーマンス検証スクリプト
 * ActionButtonsコンポーネント分離後の性能をT004ベースラインと比較
 */

import { PerformanceMetrics } from '../app/services/performance';

interface T004BaselineData {
  measurements: {
    componentMount: number;
    dataFetch: number;
    typeCardCalculation: number;
    axesScoresCalculation: number;
    totalRendering: number;
  };
  statistics: {
    componentMount: { avg: number; min: number; max: number; stdDev: number };
    dataFetch: { avg: number; min: number; max: number; stdDev: number };
    typeCardCalculation: { avg: number; min: number; max: number; stdDev: number };
    axesScoresCalculation: { avg: number; min: number; max: number; stdDev: number };
    totalRendering: { avg: number; min: number; max: number; stdDev: number };
  };
  timestamp: string;
  measurementCount: number;
}

interface T015PerformanceComparison {
  current: T004BaselineData;
  baseline: T004BaselineData;
  comparison: {
    componentMount: ComparisonResult;
    dataFetch: ComparisonResult;
    typeCardCalculation: ComparisonResult;
    axesScoresCalculation: ComparisonResult;
    totalRendering: ComparisonResult;
  };
  overallResult: {
    passed: boolean;
    withinTolerance: boolean;
    summary: string;
  };
}

interface ComparisonResult {
  currentAvg: number;
  baselineAvg: number;
  difference: number;
  percentageChange: number;
  withinTolerance: boolean; // ±5%以内
  status: 'PASS' | 'FAIL' | 'WARNING';
}

class T015PerformanceVerifier {
  private readonly TOLERANCE_PERCENTAGE = 5; // ±5%
  private readonly MEASUREMENT_COUNT = 5;
  
  /**
   * T004のベースラインデータを取得
   */
  private getT004BaselineData(): T004BaselineData | null {
    try {
      const data = localStorage.getItem('t004_baseline_complete');
      if (!data) {
        console.warn('⚠️ T004ベースラインデータが見つかりません');
        return null;
      }
      return JSON.parse(data) as T004BaselineData;
    } catch (error) {
      console.error('❌ T004ベースラインデータの読み込みエラー:', error);
      return null;
    }
  }

  /**
   * 現在のパフォーマンスを測定（T004と同じ方法）
   */
  private async measureCurrentPerformance(): Promise<T004BaselineData> {
    const measurements: any[] = [];
    
    console.log('🎯 [T015] ActionButtons分離後のパフォーマンス測定開始...');
    console.log(`📊 測定回数: ${this.MEASUREMENT_COUNT}回`);
    
    for (let i = 0; i < this.MEASUREMENT_COUNT; i++) {
      console.log(`⏱️ 測定 ${i + 1}/${this.MEASUREMENT_COUNT}...`);
      
      // 測定実行（ページリロード＋測定）
      const measurement = await this.performSingleMeasurement();
      measurements.push(measurement);
      
      // 次の測定までの間隔
      if (i < this.MEASUREMENT_COUNT - 1) {
        await this.delay(1000);
      }
    }
    
    // 統計計算
    const statistics = this.calculateStatistics(measurements);
    
    return {
      measurements: measurements[measurements.length - 1], // 最後の測定値
      statistics,
      timestamp: new Date().toISOString(),
      measurementCount: this.MEASUREMENT_COUNT
    };
  }

  /**
   * 単回測定実行
   */
  private async performSingleMeasurement(): Promise<any> {
    return new Promise((resolve) => {
      // パフォーマンス測定イベントリスナー
      const handlePerformanceData = (event: CustomEvent) => {
        window.removeEventListener('nightloom-performance-data', handlePerformanceData as any);
        resolve(event.detail);
      };
      
      window.addEventListener('nightloom-performance-data', handlePerformanceData as any);
      
      // ページリロードして測定開始
      window.location.reload();
    });
  }

  /**
   * 統計計算
   */
  private calculateStatistics(measurements: any[]): any {
    const metrics = ['componentMount', 'dataFetch', 'typeCardCalculation', 'axesScoresCalculation', 'totalRendering'];
    const statistics: any = {};
    
    metrics.forEach(metric => {
      const values = measurements.map(m => m[metric]);
      const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
      const min = Math.min(...values);
      const max = Math.max(...values);
      const variance = values.reduce((sum, val) => sum + Math.pow(val - avg, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);
      
      statistics[metric] = { avg, min, max, stdDev };
    });
    
    return statistics;
  }

  /**
   * ベースラインとの比較実行
   */
  public async performComparison(): Promise<T015PerformanceComparison | null> {
    // T004ベースラインデータ取得
    const baseline = this.getT004BaselineData();
    if (!baseline) {
      console.error('❌ T004ベースラインデータが利用できないため、比較を実行できません');
      return null;
    }
    
    console.log('✅ T004ベースラインデータ取得完了');
    console.log('📅 ベースライン測定日時:', baseline.timestamp);
    
    // 現在のパフォーマンス測定
    const current = await this.measureCurrentPerformance();
    
    // 比較実行
    const comparison = this.comparePerformance(current, baseline);
    
    const result: T015PerformanceComparison = {
      current,
      baseline,
      comparison,
      overallResult: this.evaluateOverallResult(comparison)
    };
    
    // 結果保存
    this.saveComparisonResult(result);
    
    return result;
  }

  /**
   * パフォーマンス比較
   */
  private comparePerformance(current: T004BaselineData, baseline: T004BaselineData): any {
    const metrics = ['componentMount', 'dataFetch', 'typeCardCalculation', 'axesScoresCalculation', 'totalRendering'] as const;
    const comparison: any = {};
    
    metrics.forEach(metric => {
      const currentAvg = (current.statistics as any)[metric].avg;
      const baselineAvg = (baseline.statistics as any)[metric].avg;
      const difference = currentAvg - baselineAvg;
      const percentageChange = (difference / baselineAvg) * 100;
      const withinTolerance = Math.abs(percentageChange) <= this.TOLERANCE_PERCENTAGE;
      
      let status: 'PASS' | 'FAIL' | 'WARNING' = 'PASS';
      if (!withinTolerance) {
        status = 'FAIL';
      } else if (Math.abs(percentageChange) > 2) {
        status = 'WARNING';
      }
      
      comparison[metric] = {
        currentAvg,
        baselineAvg,
        difference,
        percentageChange,
        withinTolerance,
        status
      };
    });
    
    return comparison;
  }

  /**
   * 総合結果評価
   */
  private evaluateOverallResult(comparison: any): any {
    const metrics = Object.keys(comparison);
    const allWithinTolerance = metrics.every(metric => comparison[metric].withinTolerance);
    const failedMetrics = metrics.filter(metric => comparison[metric].status === 'FAIL');
    
    let summary = '';
    if (allWithinTolerance) {
      summary = '✅ SC-003成功基準達成: 全項目が±5%以内の性能を維持';
    } else {
      summary = `❌ SC-003成功基準未達成: ${failedMetrics.length}項目が±5%を超過 (${failedMetrics.join(', ')})`;
    }
    
    return {
      passed: allWithinTolerance,
      withinTolerance: allWithinTolerance,
      summary
    };
  }

  /**
   * 比較結果保存
   */
  private saveComparisonResult(result: T015PerformanceComparison): void {
    // localStorage保存
    localStorage.setItem('t015_performance_comparison', JSON.stringify(result));
    
    // CSV用データ作成
    const csvData = this.generateCSVData(result);
    this.downloadCSV(csvData, `t015-performance-comparison-${new Date().toISOString().replace(/[:.]/g, '-')}.csv`);
    
    console.log('💾 T015比較結果を保存しました');
  }

  /**
   * CSV データ生成
   */
  private generateCSVData(result: T015PerformanceComparison): string {
    const headers = [
      'Metric',
      'Current (ms)',
      'Baseline (ms)',
      'Difference (ms)',
      'Change (%)',
      'Within Tolerance',
      'Status'
    ];
    
    const rows = Object.entries(result.comparison).map(([metric, data]: [string, any]) => [
      metric,
      data.currentAvg.toFixed(2),
      data.baselineAvg.toFixed(2),
      data.difference.toFixed(2),
      data.percentageChange.toFixed(2),
      data.withinTolerance ? 'YES' : 'NO',
      data.status
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  /**
   * CSV ダウンロード
   */
  private downloadCSV(csvContent: string, filename: string): void {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * コンソール結果表示
   */
  public displayResults(result: T015PerformanceComparison): void {
    console.log('\n🎯 ===== T015 パフォーマンス検証結果 =====');
    console.log(`📊 測定日時: ${result.current.timestamp}`);
    console.log(`📈 ベースライン: ${result.baseline.timestamp}`);
    console.log('\n📋 項目別比較結果:');
    
    Object.entries(result.comparison).forEach(([metric, data]: [string, any]) => {
      const icon = data.status === 'PASS' ? '✅' : data.status === 'WARNING' ? '⚠️' : '❌';
      console.log(`${icon} ${metric}:`);
      console.log(`   現在値: ${data.currentAvg.toFixed(2)}ms`);
      console.log(`   基準値: ${data.baselineAvg.toFixed(2)}ms`);
      console.log(`   変化率: ${data.percentageChange > 0 ? '+' : ''}${data.percentageChange.toFixed(2)}%`);
      console.log(`   許容範囲: ${data.withinTolerance ? 'YES' : 'NO'}`);
    });
    
    console.log('\n🏆 総合結果:');
    console.log(result.overallResult.summary);
    
    if (result.overallResult.passed) {
      console.log('\n🎉 ActionButtonsコンポーネント分離は性能に悪影響を与えていません！');
    } else {
      console.log('\n⚠️ 性能劣化が検出されました。最適化が必要です。');
    }
  }

  /**
   * 遅延ユーティリティ
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// エクスポート
export { T015PerformanceVerifier };
export type { T015PerformanceComparison };

// グローバル設定（ブラウザ環境で使用）
if (typeof window !== 'undefined') {
  (window as any).T015PerformanceVerifier = T015PerformanceVerifier;
}
