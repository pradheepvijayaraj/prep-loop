/**
 * Standardized typography classes for consistent styling across the app.
 * These match the design system used in dialogs and session screens.
 */
export const typography = {
  // Labels - uppercase, wide tracking
  label:
    "text-[0.625rem] font-bold uppercase tracking-widest text-muted-foreground",
  labelSubtle:
    "text-[0.625rem] font-bold uppercase tracking-widest text-muted-foreground/60",

  // Buttons
  button: "text-[0.68rem] font-bold uppercase tracking-[0.18em]",
  buttonSmall: "text-[0.625rem] font-bold uppercase tracking-[0.18em]",

  // Headers
  sectionHeader:
    "text-[0.75rem] font-bold uppercase tracking-wide text-muted-foreground/60",
  pageTitle:
    "text-[2rem] font-semibold leading-tight tracking-tight text-foreground",
  cardTitle: "text-[1rem] font-semibold tracking-tight text-foreground",

  // Metadata and badges
  metadata: "text-[0.75rem] font-medium tabular-nums text-muted-foreground/70",
  badge: "text-[0.65rem] font-semibold uppercase tracking-wide",
  badgeNumber: "text-[0.65rem] font-semibold tabular-nums",

  // Body text
  body: "text-[0.875rem] leading-relaxed text-muted-foreground/70",
  bodySmall: "text-[0.75rem] leading-relaxed text-muted-foreground/60",

  // Navigation
  navItem: "text-[0.75rem] font-medium",
  navItemActive: "text-[0.75rem] font-semibold",
} as const;
