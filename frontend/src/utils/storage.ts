export function storageGet(key: string): string | null {
  try {
    if (typeof localStorage.getItem === 'function') {
      return localStorage.getItem(key);
    }
  } catch {
    return null;
  }
  return null;
}

export function storageSet(key: string, value: string): void {
  try {
    if (typeof localStorage.setItem === 'function') {
      localStorage.setItem(key, value);
    }
  } catch {
    return;
  }
}
