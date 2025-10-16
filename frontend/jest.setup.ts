import "@testing-library/jest-dom";
import { configure } from '@testing-library/react';

// Configure React Testing Library for React 18 compatibility
configure({
  asyncUtilTimeout: 2000,
  reactStrictMode: true,
  // Improved error handling
  getElementError: (message: string | null, container: Element) => {
    const error = new Error(
      [
        message,
        'Ignored nodes: comments, script, style',
        container.innerHTML,
      ].filter(Boolean).join('\n\n'),
    );
    error.name = 'TestingLibraryElementError';
    return error;
  },
});

// Suppress React Testing Library warnings for better test output
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;
const originalConsoleLog = console.log;

console.error = (...args: any[]) => {
  // Suppress specific warnings that don't affect test functionality
  if (typeof args[0] === 'string') {
    const message = args[0];
    
    // Suppress ReactDOMTestUtils.act deprecation warning
    if (message.includes('ReactDOMTestUtils.act is deprecated') ||
        message.includes('Warning: `ReactDOMTestUtils.act` is deprecated')) {
      return;
    }
    
    // Suppress act() warnings in test environment
    if (message.includes('Warning: An update to') &&
        message.includes('was not wrapped in act(...)')) {
      return;
    }
    
    // Suppress expected test errors and logs during integration tests
    if (message.includes('結果取得エラー:') ||
        message.includes('キーワード取得エラー:') ||
        message.includes('テーマ更新エラー:') ||
        message.includes('Bootstrap failed:') ||
        message.includes('Keyword confirmation failed:') ||
        message.includes('Invalid theme ID') ||
        message.includes('falling back to fallback theme')) {
      return; // Suppress these during tests
    }
  }

  // Suppress console.log retrying messages during tests
  if (typeof args[0] === 'string' && args[0].includes('Retrying bootstrap in')) {
    return;
  }

  // Suppress console.warn for theme fallbacks during tests
  if (typeof args[0] === 'string' && args[0].includes('Invalid theme ID')) {
    return;
  }
  
  originalConsoleError(...args);
};

// Suppress console.warn for test environment
console.warn = (...args: any[]) => {
  if (typeof args[0] === 'string') {
    const message = args[0];
    
    // Suppress theme fallback warnings during tests
    if (message.includes('Invalid theme ID') ||
        message.includes('falling back to fallback theme')) {
      return;
    }
  }
  
  originalConsoleWarn(...args);
};

// Suppress console.log for test environment
console.log = (...args: any[]) => {
  if (typeof args[0] === 'string') {
    const message = args[0];
    
    // Suppress retry logs during tests
    if (message.includes('Retrying bootstrap in')) {
      return;
    }
  }
  
  originalConsoleLog(...args);
};

// Set React 18 environment flags for better compatibility
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
(globalThis as any).jest = true;

// Essential polyfills for MSW in Jest environment

// MSW v2 ClientRequest interceptor support
if (typeof global.setImmediate === 'undefined') {
  global.setImmediate = (callback: (...args: any[]) => void, ...args: any[]) =>
    setTimeout(callback, 0, ...args);
}

// Process polyfill for MSW interceptors
if (typeof global.process === 'undefined') {
  (global as any).process = {
    env: { NODE_ENV: 'test' },
    nextTick: (callback: () => void) => setTimeout(callback, 0),
    version: 'v18.0.0',
    versions: { node: '18.0.0' }
  };
}

// WebSocket polyfill for MSW v2
if (typeof global.WebSocket === 'undefined') {
  (global as any).WebSocket = class MockWebSocket extends EventTarget {
    constructor(url: string, protocols?: string | string[]) {
      super();
      (this as any).url = url;
      (this as any).protocols = protocols;
      (this as any).readyState = 1; // OPEN
    }
    
    send(data: string | ArrayBuffer) {
      // Mock implementation
    }
    
    close(code?: number, reason?: string) {
      (this as any).readyState = 3; // CLOSED
    }
    
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;
  };
}

// TextEncoder/TextDecoder - required for MSW
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder;
}

// Web Streams API - required for MSW v2
if (typeof global.ReadableStream === 'undefined') {
  try {
    // Node.js 18+ has built-in Web Streams API
    const { ReadableStream, WritableStream, TransformStream } = require('stream/web');
    global.ReadableStream = ReadableStream;
    global.WritableStream = WritableStream;
    global.TransformStream = TransformStream;
  } catch (error) {
    // For older Node.js, MSW will handle this
    console.warn('Web Streams API not available, MSW will provide fallback');
  }
}

// Fetch API mock - jest environment
global.fetch = jest.fn();

// Request/Response API - required for MSW v2
if (typeof global.Request === 'undefined') {
  // Create simple mocks for Jest environment
  (global as any).Request = class MockRequest {
    constructor(input: any, init: any = {}) {
      (this as any).url = input;
      (this as any).method = init.method || 'GET';
      (this as any).headers = new Map(Object.entries(init.headers || {}));
      (this as any).body = init.body;
    }
    
    async json() {
      const body = (this as any).body;
      return typeof body === 'string' ? JSON.parse(body) : body;
    }
    
    clone() {
      return new (global as any).Request((this as any).url, {
        method: (this as any).method,
        headers: Object.fromEntries((this as any).headers),
        body: (this as any).body
      });
    }
  };
  
  (global as any).Response = class MockResponse {
    constructor(body: any, init: any = {}) {
      (this as any).body = body;
      (this as any).status = init.status || 200;
      (this as any).statusText = init.statusText || 'OK';
      (this as any).headers = new Map(Object.entries(init.headers || {}));
    }
    
    async json() {
      const body = (this as any).body;
      return typeof body === 'string' ? JSON.parse(body) : body;
    }
    
    async text() {
      const body = (this as any).body;
      return typeof body === 'string' ? body : JSON.stringify(body);
    }
    
    clone() {
      return new (global as any).Response((this as any).body, {
        status: (this as any).status,
        statusText: (this as any).statusText,
        headers: Object.fromEntries((this as any).headers)
      });
    }
  };
  
  (global as any).Headers = class MockHeaders extends Map {
    constructor(init?: any) {
      super();
      if (init) {
        if (Array.isArray(init)) {
          for (const [key, value] of init) {
            this.set(key, value);
          }
        } else if (typeof init === 'object') {
          for (const [key, value] of Object.entries(init)) {
            this.set(key, value);
          }
        }
      }
    }
    
    append(name: string, value: string) {
      const existing = this.get(name);
      if (existing) {
        this.set(name, `${existing}, ${value}`);
      } else {
        this.set(name, value);
      }
    }
  };
}

// URL API - ensure it's available
if (typeof global.URL === 'undefined') {
  const { URL, URLSearchParams } = require('url');
  global.URL = URL;
  global.URLSearchParams = URLSearchParams;
}

// BroadcastChannel polyfill - required for MSW v2
if (typeof global.BroadcastChannel === 'undefined') {
  (global as any).BroadcastChannel = class MockBroadcastChannel extends EventTarget {
    name: string;
    
    constructor(name: string) {
      super();
      this.name = name;
    }
    
    postMessage(message: any) {
      // In test environment, we create a synthetic message event
      const event = new MessageEvent('message', {
        data: message,
        origin: 'http://localhost:3000',
        source: null,
        ports: []
      });
      
      // Dispatch to this channel instance
      this.dispatchEvent(event);
    }
    
    close() {
      // Cleanup - remove all listeners
      this.removeEventListener('message', () => {});
    }
  };
}

// MessageEvent polyfill - required for BroadcastChannel
if (typeof global.MessageEvent === 'undefined') {
  (global as any).MessageEvent = class MockMessageEvent extends Event {
    data: any;
    origin: string;
    source: any;
    ports: any[];
    
    constructor(type: string, eventInitDict?: any) {
      super(type, eventInitDict);
      this.data = eventInitDict?.data;
      this.origin = eventInitDict?.origin || '';
      this.source = eventInitDict?.source || null;
      this.ports = eventInitDict?.ports || [];
    }
  };
}

// AbortController - ensure it's available for MSW v2
if (typeof global.AbortController === 'undefined') {
  (global as any).AbortController = class MockAbortController {
    signal: AbortSignal;
    
    constructor() {
      this.signal = new (global as any).AbortSignal();
    }
    
    abort(reason?: any) {
      (this.signal as any).aborted = true;
      (this.signal as any).reason = reason;
      this.signal.dispatchEvent(new Event('abort'));
    }
  };
  
  (global as any).AbortSignal = class MockAbortSignal extends EventTarget {
    aborted: boolean = false;
    reason?: any;
    
    constructor() {
      super();
    }
    
    static abort(reason?: any) {
      const signal = new MockAbortSignal();
      signal.aborted = true;
      signal.reason = reason;
      return signal;
    }
    
    static timeout(milliseconds: number) {
      const signal = new MockAbortSignal();
      setTimeout(() => {
        signal.aborted = true;
        signal.reason = new DOMException('The operation was aborted due to timeout', 'TimeoutError');
        signal.dispatchEvent(new Event('abort'));
      }, milliseconds);
      return signal;
    }
    
    throwIfAborted() {
      if (this.aborted) {
        throw this.reason || new DOMException('The operation was aborted', 'AbortError');
      }
    }
  };
}

// DOMException - ensure it's available
if (typeof global.DOMException === 'undefined') {
  (global as any).DOMException = class MockDOMException extends Error {
    name: string;
    code?: number;
    
    constructor(message: string = '', name: string = 'Error') {
      super(message);
      this.name = name;
      
      // Add standard DOMException error codes
      const errorCodes: { [key: string]: number } = {
        'IndexSizeError': 1,
        'HierarchyRequestError': 3,
        'WrongDocumentError': 4,
        'InvalidCharacterError': 5,
        'NoModificationAllowedError': 7,
        'NotFoundError': 8,
        'NotSupportedError': 9,
        'InvalidStateError': 11,
        'SyntaxError': 12,
        'InvalidModificationError': 13,
        'NamespaceError': 14,
        'InvalidAccessError': 15,
        'TypeMismatchError': 17,
        'SecurityError': 18,
        'NetworkError': 19,
        'AbortError': 20,
        'URLMismatchError': 21,
        'QuotaExceededError': 22,
        'TimeoutError': 23,
        'InvalidNodeTypeError': 24,
        'DataCloneError': 25
      };
      
      this.code = errorCodes[name] || 0;
    }
  };
}
