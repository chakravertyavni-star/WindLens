import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { apiBaseUrl } from "./windApi.js";

describe("apiBaseUrl", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_API_BASE_URL", "");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("returns empty string when unset (same-origin /api)", () => {
    expect(apiBaseUrl()).toBe("");
  });

  it("strips trailing slash from configured origin", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com/");
    expect(apiBaseUrl()).toBe("https://api.example.com");
  });
});
