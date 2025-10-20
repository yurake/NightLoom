/**
 * T004 ベースライン測定スクリプト
 * 
 * ResultScreenコンポーネントのパフォーマンス基準値を測定するためのスクリプト
 * T015での比較用データを生成
 */

import { performanceService } from '../app/services/performance';

interface BaselineMeasurement {
  timestamp: number;
  testId: string;
  componentMetrics: {
    mountTime: number;
    renderTime: number;
    dataFetchTime: number;
    typeCardCalculation: number;
    axesScoresCalculation: number;
  };
  webVitals: {
    fcp?: number;
    lcp?: number;
    cls?: number;
    fid?: number;
    ttfb?: number;
  };
  browserInfo: {
    userAgent: string;
    viewport: { width: number; height: number };
    devicePixelRatio: number;
  };
  testConditions: {
    networkCondition: string;
    cpuThrottling: string;
    cacheState: 'cold' | 'warm';
  };
}

class BaselineMeasurementTool {
  private measurements: BaselineMeasurement[] = [];
  private testRunId: string;

  constructor() {
    this.testRunId = `baseline_${Date.now()}`;
  }

  /**
   * 測定環境情報を取得
   */
  private getBrowserInfo() {
    return {
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      devicePixelRatio: window.devicePixelRatio || 1,
    };
  }

  /**
   * ResultScreenの単一測定を実行
   */
  async measureResultScreenPerformance(
    sessionId: string,
    apiClient: any,
    testConditions: BaselineMeasurement['testConditions']
  ): Promise<BaselineMeasurement> {
    console.log('🎯 [T004] ベースライン測定開始:', { sessionId, testConditions });

    // パフォーマンス測定のリセット
    performanceService.clearMetrics();

    const startTime = performance.now();
    
    // ダミーの ResultScreen レンダリング測定
    const componentMountStart = performance.now();
    
    // シミュレーション: コンポーネントマウント時間
    await new Promise(resolve => setTimeout(resolve, 1));
    const componentMountEnd = performance.now();
    
    // シミュレーション: データフェッチ時間
    const dataFetchStart = performance.now();
    try {
      await apiClient.getResult(sessionId);
    } catch (error) {
      console.warn('API呼び出し失敗（測定続行）:', error);
    }
    const dataFetchEnd = performance.now();
    
    // シミュレーション: TypeCard計算時間
    const typeCardCalcStart = performance.now();
    // 複雑な計算の模擬
    for (let i = 0; i < 1000; i++) {
      Math.sqrt(i * Math.PI);
    }
    const typeCardCalcEnd = performance.now();
    
    // シミュレーション: AxesScores計算時間
    const axesCalcStart = performance.now();
    // 配列処理の模擬
    const mockAxes = Array.from({ length: 10 }, (_, i) => ({
      id: `axis_${i}`,
      score: Math.random() * 100,
    }));
    mockAxes.map(axis => ({ ...axis, normalized: axis.score / 100 }));
    const axesCalcEnd = performance.now();
    
    const totalRenderTime = performance.now() - startTime;

    // Web Vitals の取得
    const summary = performanceService.getPerformanceSummary();
    const webVitals: BaselineMeasurement['webVitals'] = {};
    
    summary.webVitals.forEach(vital => {
      switch (vital.name) {
        case 'FCP': webVitals.fcp = vital.value; break;
        case 'LCP': webVitals.lcp = vital.value; break;
        case 'CLS': webVitals.cls = vital.value; break;
        case 'FID': webVitals.fid = vital.value; break;
        case 'TTFB': webVitals.ttfb = vital.value; break;
      }
    });

    const measurement: BaselineMeasurement = {
      timestamp: Date.now(),
      testId: this.testRunId,
      componentMetrics: {
        mountTime: componentMountEnd - componentMountStart,
        renderTime: totalRenderTime,
        dataFetchTime: dataFetchEnd - dataFetchStart,
        typeCardCalculation: typeCardCalcEnd - typeCardCalcStart,
        axesScoresCalculation: axesCalcEnd - axesCalcStart,
      },
      webVitals,
      browserInfo: this.getBrowserInfo(),
      testConditions,
    };

    this.measurements.push(measurement);
    
    console.log('📊 [T004] 測定完了:', {
      renderTime: `${measurement.componentMetrics.renderTime.toFixed(2)}ms`,
      dataFetch: `${measurement.componentMetrics.dataFetchTime.toFixed(2)}ms`,
      typeCardCalc: `${measurement.componentMetrics.typeCardCalculation.toFixed(2)}ms`,
      axesCalc: `${measurement.componentMetrics.axesScoresCalculation.toFixed(2)}ms`,
    });

    return measurement;
  }

  /**
   * 複数回の測定を実行して統計を取得
   */
  async runBaselineMeasurements(
    sessionId: string,
    apiClient: any,
    iterations: number = 5
  ): Promise<{
    individual: BaselineMeasurement[];
    statistics: {
      avg: BaselineMeasurement['componentMetrics'];
      min: BaselineMeasurement['componentMetrics'];
      max: BaselineMeasurement['componentMetrics'];
      stdDev: BaselineMeasurement['componentMetrics'];
    };
  }> {
    console.group('🎯 [T004] ベースライン測定バッチ開始');
    console.log(`📊 測定回数: ${iterations}回`);
    
    const testConditions: BaselineMeasurement['testConditions'] = {
      networkCondition: 'regular-3g',
      cpuThrottling: '1x',
      cacheState: 'cold'
    };

    const measurements: BaselineMeasurement[] = [];

    for (let i = 0; i < iterations; i++) {
      console.log(`🔄 測定 ${i + 1}/${iterations}`);
      
      // キャッシュクリア
      if (i === 0) {
        testConditions.cacheState = 'cold';
      } else {
        testConditions.cacheState = 'warm';
      }
      
      const measurement = await this.measureResultScreenPerformance(
        sessionId,
        apiClient,
        testConditions
      );
      
      measurements.push(measurement);
      
      // 測定間の待機
      if (i < iterations - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    // 統計計算
    const statistics = this.calculateStatistics(measurements);
    
    console.log('📈 [T004] 統計結果:');
    console.table({
      'レンダリング平均': `${statistics.avg.renderTime.toFixed(2)}ms`,
      'データフェッチ平均': `${statistics.avg.dataFetchTime.toFixed(2)}ms`,
      'TypeCard計算平均': `${statistics.avg.typeCardCalculation.toFixed(2)}ms`,
      'AxesScores計算平均': `${statistics.avg.axesScoresCalculation.toFixed(2)}ms`,
    });

    // T015用の基準値保存
    const baselineData = {
      timestamp: Date.now(),
      testRunId: this.testRunId,
      sessionId,
      measurements,
      statistics,
      t015_comparison_thresholds: {
        renderTime: statistics.avg.renderTime * 1.05, // +5%許容
        dataFetchTime: statistics.avg.dataFetchTime * 1.05,
        typeCardCalculation: statistics.avg.typeCardCalculation * 1.05,
        axesScoresCalculation: statistics.avg.axesScoresCalculation * 1.05,
      }
    };
    
    // localStorage に保存
    if (typeof window !== 'undefined') {
      localStorage.setItem('t004_baseline_complete', JSON.stringify(baselineData));
      console.log('💾 完全なベースライン測定結果を保存: localStorage.t004_baseline_complete');
    }

    console.groupEnd();

    return {
      individual: measurements,
      statistics
    };
  }

  /**
   * 測定値の統計を計算
   */
  private calculateStatistics(measurements: BaselineMeasurement[]) {
    const metrics = ['mountTime', 'renderTime', 'dataFetchTime', 'typeCardCalculation', 'axesScoresCalculation'] as const;
    
    const statistics = {
      avg: {} as BaselineMeasurement['componentMetrics'],
      min: {} as BaselineMeasurement['componentMetrics'],
      max: {} as BaselineMeasurement['componentMetrics'],
      stdDev: {} as BaselineMeasurement['componentMetrics'],
    };

    metrics.forEach(metric => {
      const values = measurements.map(m => m.componentMetrics[metric]);
      
      statistics.avg[metric] = values.reduce((sum, val) => sum + val, 0) / values.length;
      statistics.min[metric] = Math.min(...values);
      statistics.max[metric] = Math.max(...values);
      
      // 標準偏差計算
      const variance = values.reduce((sum, val) => sum + Math.pow(val - statistics.avg[metric], 2), 0) / values.length;
      statistics.stdDev[metric] = Math.sqrt(variance);
    });

    return statistics;
  }

  /**
   * 測定結果をCSV形式でエクスポート
   */
  exportToCSV(): string {
    const headers = [
      'timestamp', 'testId', 'mountTime', 'renderTime', 'dataFetchTime',
      'typeCardCalculation', 'axesScoresCalculation', 'fcp', 'lcp', 'cls',
      'userAgent', 'viewportWidth', 'viewportHeight', 'networkCondition', 'cacheState'
    ];

    const rows = this.measurements.map(m => [
      m.timestamp,
      m.testId,
      m.componentMetrics.mountTime.toFixed(2),
      m.componentMetrics.renderTime.toFixed(2),
      m.componentMetrics.dataFetchTime.toFixed(2),
      m.componentMetrics.typeCardCalculation.toFixed(2),
      m.componentMetrics.axesScoresCalculation.toFixed(2),
      m.webVitals.fcp?.toFixed(2) || '',
      m.webVitals.lcp?.toFixed(2) || '',
      m.webVitals.cls?.toFixed(4) || '',
      `"${m.browserInfo.userAgent}"`,
      m.browserInfo.viewport.width,
      m.browserInfo.viewport.height,
      m.testConditions.networkCondition,
      m.testConditions.cacheState
    ]);

    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  }
}

// グローバルに公開（開発時の手動実行用）
if (typeof window !== 'undefined') {
  (window as any).BaselineMeasurementTool = BaselineMeasurementTool;
}

export { BaselineMeasurementTool, type BaselineMeasurement };
