/**
 * Frontend Performance Monitoring Service
 * 
 * Provides client-side performance tracking, metrics collection,
 * and latency monitoring for the NightLoom MVP.
 */

export interface PerformanceMetrics {
  timestamp: number;
  operation: string;
  duration: number;
  success: boolean;
  error?: string;
  metadata?: Record<string, any>;
}

export interface WebVitalsMetric {
  name: 'FCP' | 'LCP' | 'FID' | 'CLS' | 'TTFB' | 'INP';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  timestamp: number;
}

export interface ApiCallMetrics {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  success: boolean;
  timestamp: number;
  retryCount?: number;
}

class PerformanceService {
  private metrics: PerformanceMetrics[] = [];
  private apiMetrics: ApiCallMetrics[] = [];
  private webVitals: WebVitalsMetric[] = [];
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  /**
   * Initialize performance observers for Web Vitals
   */
  private initializeObservers() {
    if (typeof window === 'undefined') return;

    // Observe navigation timing
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            this.recordNavigationMetrics(entry as PerformanceNavigationTiming);
          }
        }
      });
      observer.observe({ entryTypes: ['navigation'] });
      this.observers.push(observer);
    } catch (error) {
      console.warn('Navigation timing observer not supported:', error);
    }

    // Observe paint timing
    try {
      const paintObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === 'first-contentful-paint') {
            this.recordWebVital('FCP', entry.startTime);
          }
        }
      });
      paintObserver.observe({ entryTypes: ['paint'] });
      this.observers.push(paintObserver);
    } catch (error) {
      console.warn('Paint timing observer not supported:', error);
    }

    // Observe largest contentful paint
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.recordWebVital('LCP', lastEntry.startTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(lcpObserver);
    } catch (error) {
      console.warn('LCP observer not supported:', error);
    }

    // Observe layout shift
    try {
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        if (clsValue > 0) {
          this.recordWebVital('CLS', clsValue);
        }
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);
    } catch (error) {
      console.warn('Layout shift observer not supported:', error);
    }
  }

  /**
   * Record navigation timing metrics
   */
  private recordNavigationMetrics(entry: PerformanceNavigationTiming) {
    const ttfb = entry.responseStart - entry.requestStart;
    this.recordWebVital('TTFB', ttfb);

    // Log navigation performance
    this.recordMetric('navigation', entry.loadEventEnd - entry.startTime, true, {
      domContentLoaded: entry.domContentLoadedEventEnd - entry.startTime,
      timeToFirstByte: ttfb,
      domComplete: entry.domComplete - entry.startTime,
    });
  }

  /**
   * Record Web Vital metric with rating
   */
  private recordWebVital(name: WebVitalsMetric['name'], value: number) {
    const rating = this.getWebVitalRating(name, value);
    
    const metric: WebVitalsMetric = {
      name,
      value,
      rating,
      timestamp: Date.now(),
    };

    this.webVitals.push(metric);
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${name}: ${value.toFixed(2)}ms (${rating})`);
    }
  }

  /**
   * Get Web Vital rating based on thresholds
   */
  private getWebVitalRating(name: WebVitalsMetric['name'], value: number): WebVitalsMetric['rating'] {
    const thresholds = {
      FCP: { good: 1800, poor: 3000 },
      LCP: { good: 2500, poor: 4000 },
      FID: { good: 100, poor: 300 },
      CLS: { good: 0.1, poor: 0.25 },
      TTFB: { good: 800, poor: 1800 },
      INP: { good: 200, poor: 500 },
    };

    const threshold = thresholds[name];
    if (value <= threshold.good) return 'good';
    if (value <= threshold.poor) return 'needs-improvement';
    return 'poor';
  }

  /**
   * Start timing an operation
   */
  startTiming(operation: string): () => void {
    const startTime = performance.now();
    
    return () => {
      const duration = performance.now() - startTime;
      this.recordMetric(operation, duration, true);
    };
  }

  /**
   * Record a performance metric
   */
  recordMetric(
    operation: string,
    duration: number,
    success: boolean,
    metadata?: Record<string, any>,
    error?: string
  ) {
    const metric: PerformanceMetrics = {
      timestamp: Date.now(),
      operation,
      duration,
      success,
      error,
      metadata,
    };

    this.metrics.push(metric);

    // Keep only last 1000 metrics to prevent memory issues
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }

    // Log performance issues in development
    if (process.env.NODE_ENV === 'development') {
      const threshold = this.getOperationThreshold(operation);
      if (duration > threshold) {
        console.warn(`[Performance] Slow ${operation}: ${duration.toFixed(2)}ms (threshold: ${threshold}ms)`);
      }
    }
  }

  /**
   * Get performance threshold for operation type
   */
  private getOperationThreshold(operation: string): number {
    const thresholds: Record<string, number> = {
      'api_call': 1000,
      'scene_render': 500,
      'result_calculation': 1200,
      'component_render': 100,
      'navigation': 2000,
      'bootstrap': 800,
    };

    return thresholds[operation] || 500;
  }

  /**
   * Track API call performance
   */
  trackApiCall(
    endpoint: string,
    method: string,
    startTime: number,
    status: number,
    retryCount?: number
  ): ApiCallMetrics {
    const duration = performance.now() - startTime;
    const success = status >= 200 && status < 400;

    const metrics: ApiCallMetrics = {
      endpoint,
      method,
      duration,
      status,
      success,
      timestamp: Date.now(),
      retryCount,
    };

    this.apiMetrics.push(metrics);
    this.recordMetric('api_call', duration, success, { endpoint, method, status });

    // Keep only last 500 API metrics
    if (this.apiMetrics.length > 500) {
      this.apiMetrics = this.apiMetrics.slice(-500);
    }

    return metrics;
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary(): {
    totalMetrics: number;
    averageLatency: number;
    successRate: number;
    webVitals: WebVitalsMetric[];
    recentApiCalls: ApiCallMetrics[];
    slowOperations: PerformanceMetrics[];
  } {
    const recentMetrics = this.metrics.slice(-100);
    const totalLatency = recentMetrics.reduce((sum, m) => sum + m.duration, 0);
    const successCount = recentMetrics.filter(m => m.success).length;

    const slowOperations = recentMetrics
      .filter(m => m.duration > this.getOperationThreshold(m.operation))
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 10);

    return {
      totalMetrics: this.metrics.length,
      averageLatency: totalLatency / Math.max(recentMetrics.length, 1),
      successRate: successCount / Math.max(recentMetrics.length, 1),
      webVitals: this.webVitals.slice(-10),
      recentApiCalls: this.apiMetrics.slice(-20),
      slowOperations,
    };
  }

  /**
   * Export metrics for analysis
   */
  exportMetrics(): {
    performance: PerformanceMetrics[];
    webVitals: WebVitalsMetric[];
    apiCalls: ApiCallMetrics[];
  } {
    return {
      performance: [...this.metrics],
      webVitals: [...this.webVitals],
      apiCalls: [...this.apiMetrics],
    };
  }

  /**
   * Clear all metrics
   */
  clearMetrics() {
    this.metrics = [];
    this.apiMetrics = [];
    this.webVitals = [];
  }

  /**
   * Cleanup observers
   */
  cleanup() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Global performance service instance
export const performanceService = new PerformanceService();

// Utility functions
export const measureAsync = async <T>(
  operation: string,
  fn: () => Promise<T>
): Promise<T> => {
  const endTiming = performanceService.startTiming(operation);
  try {
    const result = await fn();
    endTiming();
    return result;
  } catch (error) {
    performanceService.recordMetric(
      operation,
      0,
      false,
      undefined,
      error instanceof Error ? error.message : 'Unknown error'
    );
    throw error;
  }
};

export const measureSync = <T>(
  operation: string,
  fn: () => T
): T => {
  const endTiming = performanceService.startTiming(operation);
  try {
    const result = fn();
    endTiming();
    return result;
  } catch (error) {
    performanceService.recordMetric(
      operation,
      0,
      false,
      undefined,
      error instanceof Error ? error.message : 'Unknown error'
    );
    throw error;
  }
};
