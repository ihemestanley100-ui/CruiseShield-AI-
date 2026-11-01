/* Single global RTL cleanup hook (registered via vitest.setupFiles).
 * Unmounts rendered trees after each test so queries never see components
 * from earlier tests in the same file. The jest-dom import registers
 * matchers (toHaveTextContent, …) and, because this file is inside the
 * tsconfig include, loads their TypeScript types for every test run. */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
