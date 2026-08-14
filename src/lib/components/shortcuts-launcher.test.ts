// @vitest-environment jsdom

import { fireEvent, render, screen, within } from "@testing-library/svelte";
import { afterEach, describe, expect, it, vi } from "vitest";
import ShortcutsLauncher from "$lib/components/shortcuts-launcher.svelte";

describe("ShortcutsLauncher", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("keeps the title and close action in the same header row", async () => {
    render(ShortcutsLauncher);

    await fireEvent.click(
      screen.getByRole("button", { name: /keyboard shortcuts/i }),
    );

    const header = screen.getByTestId("shortcut-dialog-header");
    const title = screen.getByText("SHORTCUTS");
    const closeButton = screen.getByRole("button", {
      name: /close shortcuts/i,
    });

    expect(header.contains(title)).toBe(true);
    expect(header.contains(closeButton)).toBe(true);

    await fireEvent.click(closeButton);
    expect(screen.queryByText("SHORTCUTS")).toBeNull();
  });

  it("shows Ctrl K for search on Windows and Linux", async () => {
    vi.spyOn(window.navigator, "platform", "get").mockReturnValue("Win32");
    render(ShortcutsLauncher);

    await fireEvent.click(
      screen.getByRole("button", { name: /keyboard shortcuts/i }),
    );

    const row = screen.getByText("Search Questions").closest("div");
    expect(row).not.toBeNull();
    expect(within(row!).getByText("Ctrl")).toBeTruthy();
    expect(within(row!).getByText("K")).toBeTruthy();
  });

  it("shows Command K for search on Apple platforms", async () => {
    vi.spyOn(window.navigator, "platform", "get").mockReturnValue("MacIntel");
    render(ShortcutsLauncher);

    await fireEvent.click(
      screen.getByRole("button", { name: /keyboard shortcuts/i }),
    );

    const row = screen.getByText("Search Questions").closest("div");
    expect(row).not.toBeNull();
    expect(within(row!).getByText("⌘")).toBeTruthy();
    expect(within(row!).getByText("K")).toBeTruthy();
  });
});
