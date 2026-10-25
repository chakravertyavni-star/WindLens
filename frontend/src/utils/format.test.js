import { describe, expect, it } from "vitest";
import { formatCoveragePct, formatMw } from "./format.js";

describe("formatMw", () => {
  it("formats numbers with MW suffix", () => {
    expect(formatMw(2142)).toBe("2,142 MW");
  });

  it("returns em dash for null", () => {
    expect(formatMw(null)).toBe("—");
  });
});

describe("formatCoveragePct", () => {
  it("computes percentage", () => {
    expect(formatCoveragePct(744, 744)).toBe("100.0%");
  });
});
