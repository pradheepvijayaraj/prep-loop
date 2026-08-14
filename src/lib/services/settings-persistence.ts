/** Native persistence wrappers for application settings. */
import type { Settings } from "$lib/types";
import { invokeBackend } from "$lib/services/backend";

export async function loadSettings(): Promise<Settings> {
  return invokeBackend<Settings>("load_settings");
}

export async function saveSettings(settings: Partial<Settings>): Promise<void> {
  await invokeBackend("save_settings", { settings });
}
