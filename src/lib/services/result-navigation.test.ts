import { describe, expect, it } from "vitest";
import { PRELIMS_PAPER_TYPES } from "$lib/constants/upsc-catalog";
import {
  catalogReturnTo,
  catalogRouteFromSearchParams,
} from "$lib/services/catalog-model";
import { safeResultReturnTo } from "$lib/services/result-navigation";

describe("safeResultReturnTo", () => {
  it("preserves the full catalog stack behind History", () => {
    const gs1 = PRELIMS_PAPER_TYPES[0]!;
    const returnTo = catalogReturnTo({
      history: [
        { kind: "home" },
        { kind: "prelims" },
        { kind: "prelims-paper", paper: gs1 },
      ],
      screen: { kind: "prelims-history" },
    });

    expect(
      safeResultReturnTo(
        new URLSearchParams(`returnTo=${encodeURIComponent(returnTo)}`),
      ),
    ).toBe(returnTo);
    expect(
      catalogRouteFromSearchParams(
        new URL(returnTo, "https://app.local").searchParams,
      ),
    ).toMatchObject({
      screen: { kind: "prelims-history" },
      history: [
        { kind: "home" },
        { kind: "prelims" },
        { kind: "prelims-paper", paper: { id: "gs1" } },
      ],
    });
  });

  it("rejects arbitrary external and catalog destinations", () => {
    expect(
      safeResultReturnTo(new URLSearchParams("returnTo=https://example.com")),
    ).toBe("/");
    expect(
      safeResultReturnTo(new URLSearchParams("returnTo=/?screen=unknown")),
    ).toBe("/");
  });
});
