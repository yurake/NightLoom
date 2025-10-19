/**
 * ActionButtons コンポーネント関連の型定義
 * 
 * @description spec 002未完了タスクの完了対応機能で使用される
 * ActionButtonsコンポーネントのインターフェースと関連型を定義
 */

// =============================================================================
// ActionButtons Component Types
// =============================================================================

/**
 * ActionButtonsコンポーネントのプロパティ
 */
export interface ActionButtonsProps {
  /** 再診断開始時のコールバック */
  onRestart: () => void | Promise<void>;
  
  /** リトライ実行時のコールバック（オプション） */
  onRetry?: () => void | Promise<void>;
  
  /** ローディング状態 */
  isLoading?: boolean;
  
  /** ボタン無効化状態 */
  isDisabled?: boolean;
  
  /** ボタンスタイルバリアント */
  variant?: ActionButtonVariant;
  
  /** 追加CSSクラス */
  className?: string;
}

/**
 * ActionButtonsコンポーネントの内部状態
 */
export interface ActionButtonsState {
  /** 内部ローディング状態 */
  internalLoading: boolean;
  
  /** エラー状態 */
  error: string | null;
}

/**
 * ボタンスタイルのバリアント
 */
export type ActionButtonVariant = 'primary' | 'secondary';

/**
 * ボタンの状態
 */
export type ButtonState = 'idle' | 'loading' | 'disabled' | 'error';

// =============================================================================
// Implementation Progress Types
// =============================================================================

/**
 * 実装進捗チェックリストの項目
 */
export interface ImplementationChecklistItem {
  /** チェックリスト項目の識別子 */
  itemId: string;
  
  /** 所属セクション */
  section: string;
  
  /** 項目の説明 */
  description: string;
  
  /** 完了状態フラグ */
  isCompleted: boolean;
  
  /** 完了日（ISO 8601形式） */
  completedDate?: string;
  
  /** 検証方法の説明 */
  verificationMethod: string;
  
  /** 依存する他の項目のID配列 */
  dependencies?: string[];
}

/**
 * チェックリスト更新リクエスト
 */
export interface ChecklistUpdateRequest {
  /** 更新する項目のID配列 */
  itemIds: string[];
  
  /** 完了状態 */
  isCompleted: boolean;
  
  /** 完了日 */
  completedDate: string;
  
  /** 検証コメント */
  verificationComment?: string;
}

/**
 * 実装フェーズの進捗状況
 */
export interface PhaseProgress {
  /** フェーズ名 */
  phaseName: string;
  
  /** 総項目数 */
  totalItems: number;
  
  /** 完了項目数 */
  completedItems: number;
  
  /** 進捗率（0-100） */
  progressPercentage: number;
  
  /** フェーズ完了日 */
  completedDate?: string;
}

// =============================================================================
// Validation Types
// =============================================================================

/**
 * バリデーションルール
 */
export interface ValidationRule<T> {
  /** ルール名 */
  name: string;
  
  /** バリデーション関数 */
  validate: (value: T) => boolean;
  
  /** エラーメッセージ */
  errorMessage: string;
}

/**
 * バリデーション結果
 */
export interface ValidationResult {
  /** バリデーション成功フラグ */
  isValid: boolean;
  
  /** エラーメッセージ配列 */
  errors: string[];
}

// =============================================================================
// Utility Types
// =============================================================================

/**
 * コンポーネントの共通プロパティ
 */
export interface BaseComponentProps {
  /** 追加CSSクラス */
  className?: string;
  
  /** テスト用のdata-testid */
  'data-testid'?: string;
  
  /** アクセシビリティ用のaria-label */
  'aria-label'?: string;
}

/**
 * 非同期操作の状態
 */
export type AsyncOperationState = 'idle' | 'pending' | 'fulfilled' | 'rejected';

/**
 * コールバック関数の型
 */
export type AsyncCallback = () => void | Promise<void>;

/**
 * エラーハンドラーの型
 */
export type ErrorHandler = (error: Error) => void;

// =============================================================================
// Constants
// =============================================================================

/**
 * デフォルト設定値
 */
export const DEFAULT_CONFIG = {
  /** 成功基準の性能許容差（%） */
  PERFORMANCE_TOLERANCE: 5,
  
  /** デフォルトのリトライ回数 */
  DEFAULT_RETRIES: 3,
} as const;

/**
 * テストセレクター
 */
export const TEST_SELECTORS = {
  /** ActionButtonsコンポーネント */
  ACTION_BUTTONS: '[data-testid="action-buttons"]',
  
  /** 再診断ボタン */
  RESTART_BUTTON: '[data-testid="restart-button"]',
  
  /** リトライボタン */
  RETRY_BUTTON: '[data-testid="retry-button"]',
  
  /** ローディングインジケーター */
  LOADING_INDICATOR: '[data-testid="loading-indicator"]',
  
  /** エラーメッセージ */
  ERROR_MESSAGE: '[data-testid="error-message"]',
} as const;
