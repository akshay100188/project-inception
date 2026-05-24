import posthog from "posthog-js";

const KEY = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const HOST = (import.meta.env.VITE_POSTHOG_HOST as string | undefined) ?? "https://us.i.posthog.com";

export function initAnalytics() {
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
