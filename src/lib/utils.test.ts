import { describe, expect, it } from "vitest";
import {
  formatDuration,
  formatMarks,
  formatSignedMarks,
  formatTime,
  isUuid,
} from "$lib/utils";

describe("utils", () => {
  it("formats clock-style time values", () => {
    expect(formatTime(330)).toBe("5:30");
    expect(formatTime(3930)).toBe("1:05:30");
  });

  it("formats human-readable durations", () => {
    expect(formatDuration(1800)).toBe("30 min");
    expect(formatDuration(5400)).toBe("1h 30m");
  });

  it("formats marks cleanly", () => {
    expect(formatMarks(2)).toBe("2");
    expect(formatMarks(2.5)).toBe("2.5");
    expect(formatMarks(2.25)).toBe("2.25");
    expect(formatMarks(0.667)).toBe("0.667");
    expect(formatMarks(0.833)).toBe("0.833");
  });

  it("formats signed marks without noise", () => {
    expect(formatSignedMarks(2.5, "+")).toBe("+2.5");
    expect(formatSignedMarks(1, "-")).toBe("-1");
    expect(formatSignedMarks(0.667, "-")).toBe("-0.667");
    expect(formatSignedMarks(0.833, "-")).toBe("-0.833");
    expect(formatSignedMarks(0, "+")).toBe("0");
  });

  it("validates UUID values", () => {
    expect(isUuid("123e4567-e89b-12d3-a456-426614174000")).toBe(true);
    expect(isUuid("not-a-uuid")).toBe(false);
  });
});
