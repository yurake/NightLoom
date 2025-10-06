import { renderHook, act } from "@testing-library/react";
import { ThemeProvider, useTheme } from "../app/theme/ThemeProvider";

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider>{children}</ThemeProvider>
);

describe("ThemeProvider", () => {
  it("allows switching theme id", () => {
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.themeId).toBe("fallback");

    act(() => {
      result.current.setThemeId("adventure");
    });

    expect(result.current.themeId).toBe("adventure");
  });
});
