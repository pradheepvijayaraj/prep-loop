import { describe, expect, it } from "vitest";
import {
  ACTIVE_UPSC_SECTIONS,
  MAINS_PAPER_TYPES,
  PRELIMS_PAPER_TYPES,
} from "./upsc-catalog";

describe("UPSC catalog", () => {
  it("contains only the five core Mains papers and Mathematics", () => {
    expect(MAINS_PAPER_TYPES.map((paper) => paper.id)).toEqual([
      "essay",
      "gs1",
      "gs2",
      "gs3",
      "gs4",
      "math",
    ]);

    expect(MAINS_PAPER_TYPES.filter((paper) => paper.optional)).toEqual([
      expect.objectContaining({
        id: "math",
        label: "Mathematics",
        sections: ["mains-maths1", "mains-maths2"],
      }),
    ]);
  });

  it("exposes exactly the sections backed by the retained papers", () => {
    const expectedSections = [
      ...PRELIMS_PAPER_TYPES.map((paper) => paper.section),
      ...MAINS_PAPER_TYPES.flatMap((paper) => paper.sections),
    ];

    expect([...ACTIVE_UPSC_SECTIONS]).toEqual(expectedSections);
    expect(expectedSections).toHaveLength(9);
  });
});
