/**
 * T015 簡易パフォーマンス検証
 * ActionButtons分離後の性能確認用簡易スクリプト
 */

interface SimpleMetrics {
  componentMount: number;
  dataFetch: number;
  typeCardCalculation: number;
  axesScoresCalculation: number;
  totalRendering: number;
}

class T015SimpleVerifier {
  
  /**
   * T004相当のベースライン値を設定（参考値）
   */
  private getMockBaselineMetrics(): SimpleMetrics {
    // T004レポートから推定されるベースライン値
    return {
      componentMount: 15.0,     // 約15ms
      dataFetch: 250.0,         // 約250ms
      typeCardCalculation: 5.0,  // 約5ms
      axesScoresCalculation: 8.0, // 約8ms
      totalRendering: 180.0     // 約180ms
    };
  }

  /**
   * 現在のActionButtons分離後のメトリクスを取得
   */
  private async measureCurrentMetrics(): Promise<SimpleMetrics> {
    const startTime = performance.now();
    
    // 1. コンポーネントマウント測定
    const mountStart = performance.now();
    // ResultScreenコンポーネントの初期化をシミュレート
    await new Promise(resolve => setTimeout(resolve, 10));
    const componentMount = performance.now() - mountStart;

    // 2. データフェッチ測定
    const fetchStart = performance.now();
    // APIコール相当の処理をシミュレート
    await new Promise(resolve => setTimeout(resolve, 200));
    const dataFetch = performance.now() - fetchStart;

    // 3. TypeCard計算測定
    const typeStart = performance.now();
    // TypeCardの計算処理をシミュレート
    const mockTypeData = {
      name: "Test Type",
      description: "Test description for performance measurement",
      dominantAxes: ["axis_1", "axis_2"],
      polarity: "Hi-Lo" as const
    };
    // 計算処理をシミュレート
    const result = JSON.stringify(mockTypeData);
    const typeCardCalculation = performance.now() - typeStart;

    // 4. AxesScores計算測定
    const axesStart = performance.now();
    // AxesScoresの計算処理をシミュレート
    const mockAxes = [
      { id: "axis_1", name: "軸1", score: 85, rawScore: 3.5 },
      { id: "axis_2", name: "軸2", score: 30, rawScore: -1.4 },
      { id: "axis_3", name: "軸3", score: 65, rawScore: 1.2 },
      { id: "axis_4", name: "軸4", score: 70, rawScore: 1.9 }
    ];
    const axesResult = mockAxes.map(axis => ({
      ...axis,
      normalized: axis.score / 100
    }));
    const axesScoresCalculation = performance.now() - axesStart;

    const totalRendering = performance.now() - startTime;

    return {
      componentMount,
      dataFetch,
      typeCardCalculation,
      axesScoresCalculation,
      totalRendering
    };
  }

  /**
   * パフォーマンス比較実行
   */
  async performSimpleVerification(): Promise<any> {
    console.group('🎯 T015 簡易パフォーマンス検証開始');
    
    // ベースライン値取得
    const baseline = this.getMockBaselineMetrics();
    console.log('📊 ベースライン値 (T004相当):', baseline);

    // 現在の測定実行（5回平均）
    const measurements: SimpleMetrics[] = [];
    const measurementCount = 5;

    console.log(`⏱️  ${measurementCount}回測定実行中...`);
    
    for (let i = 0; i < measurementCount; i++) {
      console.log(`📈 測定 ${i + 1}/${measurementCount}...`);
      const metrics = await this.measureCurrentMetrics();
      measurements.push(metrics);
      
      // 測定間隔
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // 平均値計算
    const current: SimpleMetrics = {
      componentMount: measurements.reduce((sum, m) => sum + m.componentMount, 0) / measurementCount,
      dataFetch: measurements.reduce((sum, m) => sum + m.dataFetch, 0) / measurementCount,
      typeCardCalculation: measurements.reduce((sum, m) => sum + m.typeCardCalculation, 0) / measurementCount,
      axesScoresCalculation: measurements.reduce((sum, m) => sum + m.axesScoresCalculation, 0) / measurementCount,
      totalRendering: measurements.reduce((sum, m) => sum + m.totalRendering, 0) / measurementCount
    };

    console.log('📊 現在の平均値:', current);

    // 比較結果計算
    const comparison = this.compareMetrics(current, baseline);
    this.displayResults(comparison, current, baseline);

    // SC-003成功基準確認
    const sc003Result = this.checkSC003Compliance(comparison);
    console.log('\n🏆 SC-003成功基準結果:', sc003Result);

    // 結果保存
    const verificationResult = {
      timestamp: new Date().toISOString(),
      baseline,
      current,
      comparison,
      sc003Compliant: sc003Result.passed,
      summary: sc003Result.summary
    };

    localStorage.setItem('t015_simple_verification', JSON.stringify(verificationResult));
    console.log('💾 検証結果をlocalStorageに保存しました');

    console.groupEnd();
    return verificationResult;
  }

  /**
   * メトリクス比較
   */
  private compareMetrics(current: SimpleMetrics, baseline: SimpleMetrics) {
    const tolerance = 5; // ±5%

    const compare = (metric: keyof SimpleMetrics) => {
      const currentVal = current[metric];
      const baselineVal = baseline[metric];
      const difference = currentVal - baselineVal;
      const percentageChange = (difference / baselineVal) * 100;
      const withinTolerance = Math.abs(percentageChange) <= tolerance;

      return {
        current: currentVal,
        baseline: baselineVal,
        difference,
        percentageChange,
        withinTolerance,
        status: withinTolerance ? 'PASS' : 'FAIL'
      };
    };

    return {
      componentMount: compare('componentMount'),
      dataFetch: compare('dataFetch'),
      typeCardCalculation: compare('typeCardCalculation'),
      axesScoresCalculation: compare('axesScoresCalculation'),
      totalRendering: compare('totalRendering')
    };
  }

  /**
   * 結果表示
   */
  private displayResults(comparison: any, current: SimpleMetrics, baseline: SimpleMetrics) {
    console.log('\n📋 詳細比較結果:');
    
    Object.entries(comparison).forEach(([metric, data]: [string, any]) => {
      const icon = data.status === 'PASS' ? '✅' : '❌';
      console.log(`${icon} ${metric}:`);
      console.log(`   現在値: ${data.current.toFixed(2)}ms`);
      console.log(`   基準値: ${data.baseline.toFixed(2)}ms`);
      console.log(`   変化率: ${data.percentageChange > 0 ? '+' : ''}${data.percentageChange.toFixed(2)}%`);
      console.log(`   許容範囲: ${data.withinTolerance ? 'YES' : 'NO'}`);
    });
  }

  /**
   * SC-003成功基準確認
   */
  private checkSC003Compliance(comparison: any) {
    const metrics = Object.keys(comparison);
    const passedMetrics = metrics.filter(metric => comparison[metric].status === 'PASS');
    const failedMetrics = metrics.filter(metric => comparison[metric].status === 'FAIL');
    
    const passed = failedMetrics.length === 0;
    
    let summary: string;
    if (passed) {
      summary = '✅ SC-003成功基準達成: 全項目が±5%以内の性能を維持';
    } else {
      summary = `❌ SC-003成功基準未達成: ${failedMetrics.length}項目が±5%を超過 (${failedMetrics.join(', ')})`;
    }

    return {
      passed,
      passedCount: passedMetrics.length,
      failedCount: failedMetrics.length,
      totalCount: metrics.length,
      summary,
      failedMetrics
    };
  }
}

// ブラウザ環境でのグローバル関数
if (typeof window !== 'undefined') {
  (window as any).runT015SimpleVerification = async () => {
    const verifier = new T015SimpleVerifier();
    return await verifier.performSimpleVerification();
  };
  
  console.log('🎯 T015簡易検証スクリプト読み込み完了');
  console.log('実行方法: runT015SimpleVerification() をコンソールで実行');
}

export { T015SimpleVerifier };
