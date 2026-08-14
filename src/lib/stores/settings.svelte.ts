/**
 * Settings store (Svelte 5 runes).
 *
 * Manages user preferences (theme, navigator state, etc.) with:
 *   - One-time async initialisation from the backend (with promise lock)
 *   - Optimistic UI updates with conditional rollback on save failure
 *   - Reactive getters via `$state` runes
 *
 * Settings are loaded once at app startup (from +layout.svelte) and
 * persisted incrementally via `updateSetting`.
 */
import { type Settings, DEFAULT_SETTINGS } from "$lib/types";
import { loadSettings, saveSettings } from "$lib/services/settings-persistence";
import { logError } from "$lib/services/logger";

// Settings state using Svelte 5 runes
let settings = $state<Settings>({ ...DEFAULT_SETTINGS });
let isLoaded = $state(false);

// Promise to track ongoing initialization (prevents double-init race condition)
let initPromise: Promise<void> | null = null;

/**
 * Initialize settings from database
 * Uses a promise lock to prevent race conditions if called multiple times
 */
export async function initSettings(): Promise<void> {
  if (isLoaded) return;

  // If already initializing, wait for that to complete
  if (initPromise) {
    return initPromise;
  }

  // Create the promise synchronously before yielding to the event loop,
  // preventing double-initialization races.
  const promise = (async () => {
    try {
      const stored = await loadSettings();
      settings = { ...DEFAULT_SETTINGS, ...stored };
      isLoaded = true;
    } catch (error) {
      void logError("Failed to load settings", error);
      settings = { ...DEFAULT_SETTINGS };
      isLoaded = true;
    }
  })();

  initPromise = promise;

  try {
    await promise;
  } finally {
    initPromise = null;
  }
}

/**
 * Get current settings (reactive)
 */
export function getSettings(): Settings {
  return settings;
}

/**
 * Update a single setting
 * Includes conditional rollback on failure - only rolls back if the current
 * value still matches what we tried to save (prevents clobbering newer updates)
 */
export async function updateSetting<K extends keyof Settings>(
  key: K,
  value: Settings[K],
): Promise<void> {
  const previousValue = settings[key];
  settings[key] = value;

  try {
    await saveSettings({ [key]: value });
  } catch (error) {
    // Only rollback if current value still matches our failed write
    // (prevents clobbering a newer successful update)
    if (settings[key] === value) {
      settings[key] = previousValue;
    }
    void logError(`Failed to save setting ${key}`, error);
  }
}

// Export reactive getters for individual settings
export function getTheme(): Settings["theme"] {
  return settings.theme;
}
