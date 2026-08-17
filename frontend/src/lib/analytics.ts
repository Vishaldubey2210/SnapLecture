import posthog from "posthog-js";

let initialized = false;

export function initAnalytics(): void {
  if (initialized) {
    return;
  }

  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST;

  if (!key || !host) {
    console.warn(
      "PostHog analytics disabled: missing configuration.",
    );

    return;
  }

  posthog.init(key, {
    api_host: host,

    // Privacy-focused configuration
    autocapture: false,
    disable_session_recording: true,

    // Keep analytics anonymous unless a user is explicitly identified.
    person_profiles: "identified_only",

    capture_pageview: true,
    capture_pageleave: true,
  });

  initialized = true;
}

export function trackEvent(
  event: string,
  properties?: Record<string, unknown>,
): void {
  if (!initialized) {
    return;
  }

  posthog.capture(event, properties);
}