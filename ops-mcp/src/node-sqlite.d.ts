/**
 * Type declarations for node:sqlite (DatabaseSync).
 * Available natively in Node.js 22.5+. These stubs allow compilation
 * with @types/node@20.
 */

declare module "node:sqlite" {
  class DatabaseSync {
    constructor(path: string, options?: { open?: boolean; readOnly?: boolean });
    exec(sql: string): void;
    prepare(sql: string): StatementSync;
    close(): void;
  }

  class StatementSync {
    run(...params: unknown[]): { changes: number; lastInsertRowid: number | bigint };
    get(...params: unknown[]): unknown;
    all(...params: unknown[]): unknown[];
    iterate(...params: unknown[]): IterableIterator<unknown>;
    expandedSQL(): string;
    setAllowBareNamedParameters(enabled: boolean): void;
    setReadBigInts(enabled: boolean): void;
  }

  export { DatabaseSync, StatementSync };
}
