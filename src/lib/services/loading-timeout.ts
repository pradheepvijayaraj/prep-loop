import { SESSION_LOAD_TIMEOUT_MS } from "$lib/constants/timer";

export const LOADING_FAILURE_MESSAGE =
  "Failed. Try again. Restart if it keeps failing.";

/** Reject a slow loading operation after the shared UI loading deadline. */
export async function withLoadingTimeout<T>(operation: Promise<T>): Promise<T> {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  try {
    return await Promise.race([
      operation,
      new Promise<never>((_, reject) => {
        timeoutId = setTimeout(() => {
          reject(new Error(LOADING_FAILURE_MESSAGE));
        }, SESSION_LOAD_TIMEOUT_MS);
      }),
    ]);
  } finally {
    if (timeoutId !== null) clearTimeout(timeoutId);
  }
}
