/**
 * Shared utility functions used across the frontend.
 *
 * Includes:
 *   - `cn()` \u2014 Tailwind class merging (clsx + tailwind-merge)
 *   - Component type helpers (WithoutChild, WithElementRef, etc.)
 *   - UUID validation
 *   - Time and marks formatting
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely, resolving conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any }
  ? Omit<T, "children">
  : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & {
  ref?: U | null;
};

export const ATTEMPT_ID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isUuid(value: string): boolean {
  return ATTEMPT_ID_REGEX.test(value);
}

export function formatTime(
  seconds: number,
  style: "clock" | "human" = "clock",
): string {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (style === "human") {
    return hrs > 0 ? `${hrs}h ${mins}m` : `${mins} min`;
  }

  if (hrs > 0) {
    return `${hrs}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function formatDuration(seconds: number): string {
  return formatTime(seconds, "human");
}

export function formatMarks(value: number): string {
  if (Number.isInteger(value)) {
    return `${value}`;
  }

  return value.toFixed(3).replace(/\.?0+$/, "");
}

export function formatSignedMarks(value: number, sign: "+" | "-"): string {
  return value > 0 ? `${sign}${formatMarks(value)}` : "0";
}
