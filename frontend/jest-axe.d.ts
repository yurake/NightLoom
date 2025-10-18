import { AxeResults } from 'axe-core';

declare global {
  namespace jest {
    interface Matchers<R> {
      toHaveNoViolations(): R;
    }
  }
}

declare module 'jest-axe' {
  export function toHaveNoViolations(results: AxeResults): void;
  export function axe(container: Element, options?: any): Promise<AxeResults>;
}
