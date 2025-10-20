import * as fs from 'fs';
import * as path from 'path';

// 型定義
export interface ChecklistItem {
  id: string;
  task: string;
  completed: boolean;
  verificationMethod?: string;
  actualStatus?: 'implemented' | 'partial' | 'not-implemented';
  filePath?: string;
  lineNumber?: number;
}

export interface ChecklistSection {
  title: string;
  items: ChecklistItem[];
  phase?: string;
  estimatedTime?: string;
}

export interface ChecklistData {
  sections: ChecklistSection[];
  lastUpdated: string;
  totalItems: number;
  completedItems: number;
  progressPercentage: number;
}

export interface FileAnalysis {
  exists: boolean;
  hasTests: boolean;
  hasTypes: boolean;
  hasImplementation: boolean;
  codeQuality: 'good' | 'partial' | 'poor';
}

export interface ProgressMetrics {
  totalItems: number;
  completedItems: number;
  progressPercentage: number;
  phaseProgress: Array<{ phase: string; progress: number }>;
}

/**
 * Markdownからチェックリストデータを解析する
 */
export function parseChecklistFromMarkdown(content: string): ChecklistData {
  const lines = content.split('\n');
  const sections: ChecklistSection[] = [];
  let currentSection: ChecklistSection | null = null;
  let itemIdCounter = 1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Phase見出しの検出（## 🏗️ Phase 1: ...形式）
    if (line.match(/^##\s+🏗️\s+Phase\s+\d+:/) || line.match(/^##\s+🔌\s+Phase\s+\d+:/) || 
        line.match(/^##\s+🎨\s+Phase\s+\d+:/) || line.match(/^##\s+🧪\s+Phase\s+\d+:/)) {
      if (currentSection) {
        sections.push(currentSection);
      }
      
      const phaseMatch = line.match(/Phase\s+(\d+):\s*([^（]+)(?:（([^）]+)）)?/);
      const phase = phaseMatch ? `Phase ${phaseMatch[1]}` : '';
      const estimatedTime = phaseMatch?.[3] || '';
      
      currentSection = {
        title: line.replace(/^##\s+/, ''),
        items: [],
        phase,
        estimatedTime
      };
    }
    // その他のセクション見出しの検出
    else if (line.match(/^##\s+🎯/) || line.match(/^##\s+📊/)) {
      if (currentSection) {
        sections.push(currentSection);
      }
      
      currentSection = {
        title: line.replace(/^##\s+/, ''),
        items: [],
        phase: line.includes('🎯') ? 'Quality Gate' : 'Summary'
      };
    }

    // チェックリストアイテムの検出
    if (line.match(/^-\s+\[[ x-]\]/)) {
      if (!currentSection) {
        // セクションが未定義の場合、デフォルトセクションを作成
        currentSection = {
          title: 'その他',
          items: [],
          phase: 'Other'
        };
      }

      const completed = line.includes('[x]');
      const taskText = line.replace(/^-\s+\[[ x-]\]\s*/, '');
      
      // ファイルパスの抽出（[`path`](path)形式）
      const filePathMatch = taskText.match(/\[`([^`]+)`\]\(([^)]+)\)/);
      const filePath = filePathMatch ? filePathMatch[2] : undefined;
      
      // 検証方法の抽出（(`command`)形式）
      const verificationMatch = taskText.match(/\(`([^`]+)`\)/);
      const verificationMethod = verificationMatch ? verificationMatch[1] : undefined;
      
      // タスク名の抽出（マークダウン記法を除去）
      const cleanTask = taskText
        .replace(/\[`[^`]+`\]\([^)]+\)/g, '')  // ファイルパスリンクを除去
        .replace(/\(`[^`]+`\)/g, '')         // 検証方法を除去
        .replace(/\s+/g, ' ')               // 連続スペースを単一スペースに
        .trim();

      const item: ChecklistItem = {
        id: `item-${itemIdCounter++}`,
        task: cleanTask,
        completed,
        verificationMethod,
        filePath
      };

      currentSection.items.push(item);
    }
  }

  // 最後のセクションを追加
  if (currentSection) {
    sections.push(currentSection);
  }

  // 進捗計算
  const totalItems = sections.reduce((sum, section) => sum + section.items.length, 0);
  const completedItems = sections.reduce((sum, section) => 
    sum + section.items.filter(item => item.completed).length, 0);
  const progressPercentage = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  return {
    sections,
    lastUpdated: new Date().toISOString(),
    totalItems,
    completedItems,
    progressPercentage
  };
}

/**
 * 実装状況を確認する
 */
export async function verifyImplementationStatus(item: ChecklistItem): Promise<'implemented' | 'partial' | 'not-implemented'> {
  // ファイルパスが指定されている場合
  if (item.filePath) {
    try {
      const analysis = await analyzeFileImplementation(item.filePath);
      
      if (!analysis.exists) {
        return 'not-implemented';
      }
      
      // ファイルの品質に基づく判定
      if (analysis.codeQuality === 'good' && analysis.hasImplementation) {
        return 'implemented';
      } else if (analysis.hasImplementation) {
        return 'partial';
      } else {
        return 'not-implemented';
      }
    } catch (error) {
      return 'not-implemented';
    }
  }

  // 検証方法が指定されている場合（コマンド実行系）
  if (item.verificationMethod) {
    // コマンド系のタスクは手動確認が必要なため、現状では部分実装として扱う
    return 'partial';
  }

  // その他の場合は手動確認が必要
  return 'partial';
}

/**
 * チェックリストアイテムを更新する
 */
export function updateChecklistItem(item: ChecklistItem, status: boolean): ChecklistItem {
  return {
    ...item,
    completed: status
  };
}

/**
 * ファイル実装を分析する
 */
export async function analyzeFileImplementation(filePath: string): Promise<FileAnalysis> {
  // プロジェクトルートからの相対パスで解決
  // テスト実行時はfrontendディレクトリがcwdになるため、一つ上のディレクトリに移動
  const projectRoot = process.cwd().includes('frontend') ? path.join(process.cwd(), '..') : process.cwd();
  const fullPath = path.resolve(projectRoot, filePath);
  
  try {
    // ファイルの存在確認
    if (!fs.existsSync(fullPath)) {
      return {
        exists: false,
        hasTests: false,
        hasTypes: false,
        hasImplementation: false,
        codeQuality: 'poor'
      };
    }

    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.split('\n');
    
    // テストファイルかどうかの判定
    const isTestFile = filePath.includes('.test.') || filePath.includes('/tests/');
    
    // 実装品質の分析
    const hasImports = content.includes('import ') || content.includes('require(');
    const hasExports = content.includes('export ') || content.includes('module.exports');
    const hasTypeDefinitions = content.includes('interface ') || content.includes('type ') || 
                              content.includes(': React.') || filePath.endsWith('.ts') || filePath.endsWith('.tsx');
    
    // 実装密度の計算（空行とコメントを除いた行数）
    const codeLines = lines.filter(line => {
      const trimmed = line.trim();
      return trimmed.length > 0 && 
             !trimmed.startsWith('//') && 
             !trimmed.startsWith('/*') && 
             !trimmed.startsWith('*');
    }).length;
    
    // テストケースの有無（テストファイルの場合）
    const hasTestCases = isTestFile && (
      content.includes('test(') || 
      content.includes('it(') || 
      content.includes('describe(')
    );
    
    // 実装の有無
    const hasImplementation = codeLines > 5 && (hasImports || hasExports);
    
    // 品質判定
    let codeQuality: 'good' | 'partial' | 'poor';
    if (isTestFile) {
      // テストファイルの品質判定
      codeQuality = hasTestCases && codeLines > 10 ? 'good' : 
                   hasTestCases ? 'partial' : 'poor';
    } else {
      // 実装ファイルの品質判定
      codeQuality = hasImplementation && hasTypeDefinitions && codeLines > 20 ? 'good' :
                   hasImplementation ? 'partial' : 'poor';
    }
    
    return {
      exists: true,
      hasTests: isTestFile ? hasTestCases : false,
      hasTypes: hasTypeDefinitions,
      hasImplementation,
      codeQuality
    };
    
  } catch (error) {
    return {
      exists: false,
      hasTests: false,
      hasTypes: false,
      hasImplementation: false,
      codeQuality: 'poor'
    };
  }
}

/**
 * 進捗メトリクスを計算する
 */
export function calculateProgressMetrics(sections: ChecklistSection[]): ProgressMetrics {
  const totalItems = sections.reduce((sum, section) => sum + section.items.length, 0);
  const completedItems = sections.reduce((sum, section) => 
    sum + section.items.filter(item => item.completed).length, 0);
  
  const progressPercentage = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  
  // フェーズ別進捗
  const phaseProgress = sections.map(section => {
    const sectionTotal = section.items.length;
    const sectionCompleted = section.items.filter(item => item.completed).length;
    const progress = sectionTotal > 0 ? Math.round((sectionCompleted / sectionTotal) * 10000) / 100 : 0;
    
    return {
      phase: section.phase || section.title,
      progress
    };
  });
  
  return {
    totalItems,
    completedItems,
    progressPercentage,
    phaseProgress
  };
}

/**
 * Markdownチェックリストを更新する
 */
export function updateChecklistMarkdown(content: string, updates: Array<{ id: string; completed: boolean }>): string {
  const lines = content.split('\n');
  const updatedLines: string[] = [];
  const updateMap = new Map(updates.map(u => [u.id, u.completed]));
  let itemIdCounter = 1;
  
  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    
    // チェックリストアイテムの更新
    if (line.match(/^-\s+\[[ x-]\]/)) {
      const itemId = `item-${itemIdCounter++}`;
      
      if (updateMap.has(itemId)) {
        const shouldComplete = updateMap.get(itemId);
        if (shouldComplete) {
          line = line.replace(/^-\s+\[[ -]\]/, '- [x]');
        } else {
          line = line.replace(/^-\s+\[x\]/, '- [ ]');
        }
      }
    }
    
    // 完了日フィールドの更新
    if (line.includes('**完了日**: ___________')) {
      // セクション内に完了したアイテムがある場合、現在日付を設定
      const hasCompletedInSection = updates.some(u => u.completed);
      if (hasCompletedInSection) {
        const today = new Date().toISOString().split('T')[0];
        line = line.replace('___________', today);
      }
    }
    
    // 進捗サマリーの更新
    if (line.includes('**実装完了**: _____')) {
      // 進捗率を計算して更新
      const totalUpdates = updates.length;
      const completedUpdates = updates.filter(u => u.completed).length;
      const progress = totalUpdates > 0 ? Math.round((completedUpdates / totalUpdates) * 100) : 0;
      line = line.replace('_____', progress.toString());
    }
    
    updatedLines.push(line);
  }
  
  return updatedLines.join('\n');
}

// デフォルトエクスポート用のオブジェクト
export const checklistVerification = {
  parseChecklistFromMarkdown,
  verifyImplementationStatus,
  updateChecklistItem,
  updateChecklistMarkdown,
  analyzeFileImplementation,
  calculateProgressMetrics
};

export default checklistVerification;
