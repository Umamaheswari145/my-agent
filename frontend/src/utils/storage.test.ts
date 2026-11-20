import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { storageGet, storageSet } from './storage';

describe('storage helpers', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('reads and writes values', () => {
    storageSet('key', 'value');
    expect(storageGet('key')).toBe('value');
    expect(storageGet('missing')).toBeNull();
  });

  it('returns null when storage throws', () => {
    vi.spyOn(window.localStorage, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(window.localStorage, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });

    expect(storageGet('key')).toBeNull();
    expect(() => storageSet('key', 'value')).not.toThrow();
  });
});
