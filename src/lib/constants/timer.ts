/**
 * Timer-related constants for the test session.
 *
 * Centralised here so they can be tuned without touching business logic.
 * Changing these values affects battery/CPU usage and resume accuracy:
 * - Lower `TIMER_PERSIST_INTERVAL_SECONDS` = more DB writes but more
 *   accurate resume on crash/force-quit.
 * - Lower `TIMER_TICK_MS` = smoother countdown but higher CPU overhead.
 */

/**
 * How often (in seconds) the remaining time is persisted to the backend.
 *
 * 30s is a good balance: a user who force-quits loses at most 30s of
 * timer progress on resume, while only writing to SQLite ~2×/minute.
 */
export const TIMER_PERSIST_INTERVAL_SECONDS = 30;

/**
 * Interval (in milliseconds) between timer ticks during a test.
 *
 * 1000ms (1 second) matches the granularity of the timer display.
 * Sub-second precision adds complexity without visual benefit.
 */
export const TIMER_TICK_MS = 1000;

/** Maximum time a route waits for the native session payload. */
export const SESSION_LOAD_TIMEOUT_MS = 20_000;
