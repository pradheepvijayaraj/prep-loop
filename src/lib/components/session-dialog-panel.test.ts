// @vitest-environment jsdom

import { render, screen, waitFor } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import SessionDialogPanelHarness from "$lib/components/test-helpers/session-dialog-panel-harness.svelte";

describe("SessionDialogPanel", () => {
  it("does not render a redundant footer cancel action", () => {
    render(SessionDialogPanelHarness);

    expect(screen.queryByRole("button", { name: "Back" })).toBeNull();
    expect(screen.getByRole("button", { name: "Delete" })).toBeTruthy();
  });

  it("focuses the primary action when requested", async () => {
    render(SessionDialogPanelHarness, {
      props: {
        initialFocus: "primary",
      },
    });

    const primaryButton = screen.getByRole("button", { name: "Delete" });

    await waitFor(() => {
      expect(document.activeElement).toBe(primaryButton);
    });
  });

  it("focuses the close action by default", async () => {
    render(SessionDialogPanelHarness);

    const closeButton = screen.getByRole("button", { name: "Close dialog" });

    await waitFor(() => {
      expect(document.activeElement).toBe(closeButton);
    });
  });

  it("falls back to the primary action when all cancel affordances are disabled", async () => {
    render(SessionDialogPanelHarness, {
      props: {
        secondaryDisabled: true,
      },
    });

    const primaryButton = screen.getByRole("button", { name: "Delete" });

    await waitFor(() => {
      expect(document.activeElement).toBe(primaryButton);
    });
  });
});
