/**
 * Performance Measurement Utilities
 * 
 * 500ms要件検証のためのパフォーマンス計測ユーティリティ
 * performance.mark/measure APIを使用した精密な測定
 */

/**
 * パフォーマンス測定の開始マーク
 */
export const PERFORMANCE_MARKS = {
  RESULT_SCREEN_START: 'result-screen-start',
  RESULT_SCREEN_END: 'result-screen-end',
  API_CALL_START: 'api-call-start',
  API_CALL_END: 'api-call-end',
  TYPE_CARD_RENDER_START: 'type-card-render-start',
  TYPE_CARD_RENDER_END: 'type-card-render-end',
  AXES_SCORES_RENDER_START: 'axes-scores-render-start',
  AXES_SCORES_RENDER_END: 'axes-scores-render-end',
  ANIMATION_START: 'animation-start',
  ANIMATION_END: 'animation-end',
} as const;

export type PerformanceMark = typeof PERFORMANCE_MARKS[keyof typeof PERFORMANCE_MARKS];

/**
 * パフォーマンス測定の結果
 */
export interface PerformanceMeasurement {
  name: string;
  duration: number;
  startTime: number;
  endTime: number;
  meets500msRequirement: boolean;
}

/**
 * パフォーマンス測定サマリー
 */
export interface PerformanceSummary {
  totalDuration: number;
  measurements: PerformanceMeasurement[];
  requirementsMet: boolean;
  slowestOperation: PerformanceMeasurement | null;
  fastestOperation: PerformanceMeasurement | null;
}

/**
 * パフォーマンスマークを作成
 * @param markName マーク名
 */
export function createPerformanceMark(markName: PerformanceMark): void {
  if (typeof performance !== 'undefined' && performance.mark) {
    try {
      performance.mark(markName);
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`📊 Performance Mark: ${markName} at ${Date.now()}`);
      }
    } catch (error) {
      console.warn('Failed to create performance mark:', error);
    }
  }
}

/**
 * パフォーマンス測定を実行
 * @param measureName 測定名
 * @param startMark 開始マーク名
 * @param endMark 終了マーク名
 * @returns 測定結果
 */
export function measurePerformance(
  measureName: string,
  startMark: PerformanceMark,
  endMark: PerformanceMark
): PerformanceMeasurement | null {
  if (typeof performance === 'undefined' || !performance.measure) {
    return null;
  }

  try {
    // 測定実行
    performance.measure(measureName, startMark, endMark);
    
    // 結果取得
    const entries = performance.getEntriesByName(measureName, 'measure');
    const latestEntry = entries[entries.length - 1];
    
    if (!latestEntry) {
      return null;
    }

    const measurement: PerformanceMeasurement = {
      name: measureName,
      duration: latestEntry.duration,
      startTime: latestEntry.startTime,
      endTime: latestEntry.startTime + latestEntry.duration,
      meets500msRequirement: latestEntry.duration <= 500
    };

    if (process.env.NODE_ENV === 'development') {
      const status = measurement.meets500msRequirement ? '✅' : '❌';
      console.log(`📊 Performance Measure: ${measureName} - ${measurement.duration.toFixed(2)}ms ${status}`);
    }

    return measurement;
  } catch (error) {
    console.warn('Failed to measure performance:', error);
    return null;
  }
}

/**
 * ResultScreen の初期レンダリング測定開始
 */
export function startResultScreenMeasurement(): void {
  createPerformanceMark(PERFORMANCE_MARKS.RESULT_SCREEN_START);
}

/**
 * ResultScreen の初期レンダリング測定完了
 * @returns 測定結果
 */
export function endResultScreenMeasurement(): PerformanceMeasurement | null {
  createPerformanceMark(PERFORMANCE_MARKS.RESULT_SCREEN_END);
  return measurePerformance(
    'result-screen-render',
    PERFORMANCE_MARKS.RESULT_SCREEN_START,
    PERFORMANCE_MARKS.RESULT_SCREEN_END
  );
}

/**
 * API呼び出し測定開始
 */
export function startApiCallMeasurement(): void {
  createPerformanceMark(PERFORMANCE_MARKS.API_CALL_START);
}

/**
 * API呼び出し測定完了
 * @returns 測定結果
 */
export function endApiCallMeasurement(): PerformanceMeasurement | null {
  createPerformanceMark(PERFORMANCE_MARKS.API_CALL_END);
  return measurePerformance(
    'api-call-duration',
    PERFORMANCE_MARKS.API_CALL_START,
    PERFORMANCE_MARKS.API_CALL_END
  );
}

/**
 * アニメーション測定開始
 */
export function startAnimationMeasurement(): void {
  createPerformanceMark(PERFORMANCE_MARKS.ANIMATION_START);
}

/**
 * アニメーション測定完了
 * @returns 測定結果
 */
export function endAnimationMeasurement(): PerformanceMeasurement | null {
  createPerformanceMark(PERFORMANCE_MARKS.ANIMATION_END);
  return measurePerformance(
    'animation-duration',
    PERFORMANCE_MARKS.ANIMATION_START,
    PERFORMANCE_MARKS.ANIMATION_END
  );
}

/**
 * 全パフォーマンス測定結果を取得
 * @returns 測定サマリー
 */
export function getPerformanceSummary(): PerformanceSummary {
  if (typeof performance === 'undefined') {
    return {
      totalDuration: 0,
      measurements: [],
      requirementsMet: true,
      slowestOperation: null,
      fastestOperation: null
    };
  }

  try {
    // 全ての測定結果を取得
    const measures = performance.getEntriesByType('measure') as PerformanceEntry[];
    const measurements: PerformanceMeasurement[] = measures.map(entry => ({
      name: entry.name,
      duration: entry.duration,
      startTime: entry.startTime,
      endTime: entry.startTime + entry.duration,
      meets500msRequirement: entry.duration <= 500
    }));

    // 統計計算
    const totalDuration = measurements.reduce((sum, m) => sum + m.duration, 0);
    const requirementsMet = measurements.every(m => m.meets500msRequirement);
    
    const slowestOperation = measurements.reduce((slowest, current) => 
      !slowest || current.duration > slowest.duration ? current : slowest, 
      null as PerformanceMeasurement | null
    );
    
    const fastestOperation = measurements.reduce((fastest, current) => 
      !fastest || current.duration < fastest.duration ? current : fastest,
      null as PerformanceMeasurement | null
    );

    return {
      totalDuration,
      measurements,
      requirementsMet,
      slowestOperation,
      fastestOperation
    };
  } catch (error) {
    console.warn('Failed to get performance summary:', error);
    return {
      totalDuration: 0,
      measurements: [],
      requirementsMet: true,
      slowestOperation: null,
      fastestOperation: null
    };
  }
}

/**
 * パフォーマンス測定結果をコンソールに出力
 */
export function logPerformanceSummary(): void {
  if (process.env.NODE_ENV !== 'development') {
    return;
  }

  const summary = getPerformanceSummary();
  
  console.group('📊 NightLoom Performance Summary');
  console.log(`Total Duration: ${summary.totalDuration.toFixed(2)}ms`);
  console.log(`Requirements Met: ${summary.requirementsMet ? '✅' : '❌'}`);
  
  if (summary.slowestOperation) {
    console.log(`Slowest: ${summary.slowestOperation.name} (${summary.slowestOperation.duration.toFixed(2)}ms)`);
  }
  
  if (summary.fastestOperation) {
    console.log(`Fastest: ${summary.fastestOperation.name} (${summary.fastestOperation.duration.toFixed(2)}ms)`);
  }
  
  console.table(summary.measurements.map(m => ({
    Operation: m.name,
    Duration: `${m.duration.toFixed(2)}ms`,
    'Meets 500ms': m.meets500msRequirement ? '✅' : '❌'
  })));
  
  console.groupEnd();
}

/**
 * パフォーマンス測定をクリア
 */
export function clearPerformanceMeasurements(): void {
  if (typeof performance !== 'undefined' && performance.clearMeasures) {
    try {
      performance.clearMeasures();
      performance.clearMarks();
      
      if (process.env.NODE_ENV === 'development') {
        console.log('📊 Performance measurements cleared');
      }
    } catch (error) {
      console.warn('Failed to clear performance measurements:', error);
    }
  }
}

/**
 * 自動パフォーマンス測定フック
 * コンポーネントのマウント時間を自動測定
 */
export function usePerformanceMeasurement(componentName: string) {
  if (typeof window === 'undefined') {
    return { startMeasurement: () => {}, endMeasurement: () => null };
  }

  const startMarkName = `${componentName}-start` as PerformanceMark;
  const endMarkName = `${componentName}-end` as PerformanceMark;

  const startMeasurement = () => {
    createPerformanceMark(startMarkName);
  };

  const endMeasurement = () => {
    createPerformanceMark(endMarkName);
    return measurePerformance(
      `${componentName}-render`,
      startMarkName,
      endMarkName
    );
  };

  return { startMeasurement, endMeasurement };
}
