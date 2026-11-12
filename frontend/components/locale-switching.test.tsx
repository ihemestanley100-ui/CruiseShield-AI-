import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DecisionForm } from "./decision-form";
import { LoginCard } from "./login-gate";
import { WorkflowStrip } from "./workflow-strip";
import {
  LOCALE_STORAGE_KEY,
  LocaleProvider,
} from "../lib/i18n/context";
import { clearMissingKeys, getMissingKeys } from "../lib/i18n/dictionaries";
import { GlobalLandingPage } from "./landing/GlobalLandingPage";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/platform",
}));

vi.mock("./landing/GlobalHeroScene", () => ({
  GlobalHeroScene: () => <div data-testid="hero-stub" />,
}));

afterEach(() => {
  window.localStorage.clear();
  document.documentElement.lang = "en";
  document.documentElement.dir = "ltr";
  clearMissingKeys();
});

function texts(): string {
  return document.body.textContent ?? "";
}

describe("locale switching integration", () => {
  it.each([
    "en",
    "fr",
    "ar",
    "ig",
    "yo",
    "ha",
    "pt",
    "es",
    "zh",
    "hi",
    "sw",
    "ja",
  ])("renders shell chrome in %s with no missing-key markers", (locale) => {
      window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
      render(
        <LocaleProvider>
          <WorkflowStrip
            invId="inv_84721"
            txnId="txn_84721"
            caseId="case_84721"
            scenarioId="scn_primary"
          />
          <LoginCard onLogin={async () => null} />
          <DecisionForm
            caseId="case_84721"
            allowedTransitions={["open", "closed"]}
            onDecided={() => {}}
          />
          <GlobalLandingPage />
        </LocaleProvider>
      );
      expect(texts()).not.toMatch(/\[[a-z]+\.[A-Za-z0-9_.]+\]/);
      expect(getMissingKeys()).toEqual([]);
    }
  );

  it("translates the landing hero while keeping brand and routes intact", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    render(
      <LocaleProvider>
        <GlobalLandingPage />
      </LocaleProvider>
    );
    expect(screen.getByRole("heading", { name: "Un monde financier plus sûr" }))
      .toBeTruthy();
    expect(screen.getByText("DÉTECTER")).toBeTruthy();
    // Brand stays verbatim; platform links still target real routes.
    expect(screen.getAllByText("CruiseShield AI™").length).toBeGreaterThan(0);
    const cta = screen.getAllByRole("link", { name: /Explorer CruiseShield AI/ })[0];
    expect(cta?.getAttribute("href")).toBe("/platform");
  });

  it("keeps server-contract decision labels verbatim in every locale", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "ar");
    render(
      <LocaleProvider>
        <DecisionForm
          caseId="case_84721"
          allowedTransitions={["open"]}
          onDecided={() => {}}
        />
      </LocaleProvider>
    );
    // Chrome translates; submitted values never do (server rejects others).
    expect(screen.getByText("قرار بشري")).toBeTruthy();
    for (const label of [
      "Close Case",
      "Escalate",
      "Mark False Positive",
      "Monitor",
      "Request Verification",
    ]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });

  it("switches to RTL layout for Arabic and back for French", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "ar");
    const { unmount } = render(
      <LocaleProvider>
        <WorkflowStrip
          invId="inv_84721"
          txnId="txn_84721"
          caseId="case_84721"
          scenarioId="scn_primary"
        />
      </LocaleProvider>
    );
    expect(document.documentElement.dir).toBe("rtl");
    expect(document.documentElement.lang).toBe("ar");
    expect(screen.getByText("اكتشاف")).toBeTruthy();
    unmount();
    // Simulated navigation: remount reads the persisted locale.
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    render(
      <LocaleProvider>
        <WorkflowStrip
          invId="inv_84721"
          txnId="txn_84721"
          caseId="case_84721"
          scenarioId="scn_primary"
        />
      </LocaleProvider>
    );
    expect(document.documentElement.dir).toBe("ltr");
    expect(screen.getByText("Détecter")).toBeTruthy();
  });

  it("falls back to English for untranslated locales without markers", () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "zu");
    render(
      <LocaleProvider>
        <WorkflowStrip
          invId="inv_84721"
          txnId="txn_84721"
          caseId="case_84721"
          scenarioId="scn_primary"
        />
      </LocaleProvider>
    );
    expect(screen.getByText("Detect")).toBeTruthy();
    expect(texts()).not.toMatch(/\[[a-z]+\.[A-Za-z0-9_.]+\]/);
  });

  it("renders full drafts with no English fallback and no ledger gaps", () => {
    // UGLS final: every dictionaried locale is fully drafted, so
    // formerly-falling-back keys now render translated. (Whole-locale
    // fallback for undictionaried tags is still covered by the zu test.)
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "yo");
    render(
      <LocaleProvider>
        <DecisionForm
          caseId="case_84721"
          allowedTransitions={["open", "closed"]}
          onDecided={() => {}}
        />
      </LocaleProvider>
    );
    expect(screen.getByText("Ìpinnu ènìyàn")).toBeTruthy();
    expect(screen.getByText("Yan ìpinnu…")).toBeTruthy();
    expect(texts()).not.toMatch(/\[[a-z]+\.[A-Za-z0-9_.]+\]/);
    expect(getMissingKeys()).toEqual([]);
  });
});
