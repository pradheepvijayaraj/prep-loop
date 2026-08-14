import { isCatalogReturnTo } from "$lib/services/catalog-model";

/** Restrict result return links to known in-app destinations. */
export function safeResultReturnTo(searchParams: URLSearchParams): string {
  const value = searchParams.get("returnTo") ?? "";
  return value === "/" ||
    isCatalogReturnTo(value) ||
    value.startsWith("/results")
    ? value
    : "/";
}
