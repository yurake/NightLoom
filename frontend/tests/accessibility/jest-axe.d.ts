declare module 'jest-axe' {
  export function axe(container: Element | Document, options?: any): Promise<any>;
  export const toHaveNoViolations: any;
}
