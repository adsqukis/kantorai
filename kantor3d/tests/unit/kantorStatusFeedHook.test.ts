import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const fetchMock = vi.fn();
vi.mock("@/lib/runtime/custom/http", () => ({
  fetchCustomRuntimeJson: (...args: unknown[]) => fetchMock(...args),
}));

import { useKantorStatusFeed } from "@/lib/kantor/useKantorStatusFeed";

afterEach(() => {
  fetchMock.mockReset();
  vi.useRealTimers();
});

describe("useKantorStatusFeed", () => {
  it("keeps the last statuses when the runtime goes down", async () => {
    vi.useFakeTimers();
    fetchMock.mockResolvedValueOnce({ agent_status: { tiktok: "kerja" } });
    fetchMock.mockRejectedValue(new Error("runtime mati"));
    const { result } = renderHook(() => useKantorStatusFeed("http://127.0.0.1:8081", 1000));
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current).toEqual({ tiktok: "working" });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8081", "/state");
    expect(result.current).toEqual({ tiktok: "working" });
  });

  it("does nothing without a runtime url", () => {
    const { result } = renderHook(() => useKantorStatusFeed(null));
    expect(result.current).toEqual({});
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
