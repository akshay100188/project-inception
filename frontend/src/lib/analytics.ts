import posthog from "posthog-js";

const KEY = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const HOST = (import.meta.env.VITE_POSTHOG_HOST as string | undefined) ?? "https://us.i.posthog.com";

// Central Umami analytics — loads independently of PostHog; dormant until both
// VITE_UMAMI_SRC and VITE_UMAMI_WEBSITE_ID are set at build time.
const UMAMI_SRC = import.meta.env.VITE_UMAMI_SRC as string | undefined;
const UMAMI_WEBSITE_ID = import.meta.env.VITE_UMAMI_WEBSITE_ID as string | undefined;

function initUmami() {
  if (!UMAMI_SRC || !UMAMI_WEBSITE_ID) return;
  if (document.querySelector("script[data-umami]")) return; // avoid double-inject
  const s = document.createElement("script");
  s.defer = true;
  s.src = UMAMI_SRC;
  s.setAttribute("data-website-id", UMAMI_WEBSITE_ID);
  s.setAttribute("data-umami", "true");
  document.head.appendChild(s);
}

export function initAnalytics() {
  initUmami();
  if (!KEY) return;
  posthog.init(KEY, {
    api_host: HOST,
    capture_pageview: true,   // auto page views
    capture_pageleave: true,  // tracks time on page
    autocapture: false,       // explicit events only — keeps data clean
    persistence: "localStorage",
  });
}

export function identifyUser(userId: string, properties?: Record<string, unknown>) {
  if (!KEY) return;
  posthog.identify(userId, properties);
}

export function track(event: string, properties?: Record<string, unknown>) {
  if (!KEY) return;
  posthog.capture(event, properties);
}

export function resetUser() {
  if (!KEY) return;
  posthog.reset();
}
