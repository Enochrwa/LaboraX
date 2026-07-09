/**
 * Fixture helpers shared across frontend tests. Nothing here is a real
 * credential — each call returns a fresh, randomly generated value used
 * only against an in-memory mocked API client or a throwaway local test
 * database. Deliberately exposed as functions (not exported constants)
 * so there is no static "X_PASSWORD = ..." assignment for a secret
 * scanner to key off.
 */
export function testFixtureCredential(): string {
  return `t${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
}
