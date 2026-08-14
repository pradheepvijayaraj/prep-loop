<!--
  Catalog navigation tile.
  size:
    - lg  home stage cards (Prelims / Mains)
    - md  paper-type cards (Essay, GS1…)
    - sm  year / paper instance cards
-->
<script lang="ts">
  import { cn } from "$lib/utils";

  interface Props {
    title: string;
    eyebrow?: string;
    description?: string;
    meta?: string;
    asideValue?: string;
    asideLabel?: string;
    index?: number;
    size?: "lg" | "md" | "sm";
    class?: string;
    onclick?: () => void;
  }

  let {
    title,
    eyebrow = "",
    description = "",
    meta = "",
    asideValue = "",
    asideLabel = "",
    index = 0,
    size = "md",
    class: className = "",
    onclick,
  }: Props = $props();
</script>

<button
  type="button"
  class={cn(
    "app-surface-enter relative flex w-full cursor-pointer flex-col border border-border/75 bg-card/35 text-left",
    "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-foreground/75",
    size === "lg" &&
      "min-h-[10.25rem] justify-center p-6 sm:min-h-[11rem] sm:p-7",
    size === "md" && "min-h-[7rem] justify-center p-5 sm:p-6",
    size === "sm" && "min-h-[5.5rem] justify-center p-4 sm:p-5",
    className,
  )}
  style={`--enter-delay: ${Math.min(index * 22, 160)}ms;`}
  {onclick}
>
  <div
    class={cn(
      "relative z-10 flex min-w-0 flex-1 flex-col justify-center",
      asideValue && "pr-28 sm:pr-36",
    )}
  >
    {#if eyebrow}
      <span
        class="mb-2 text-[0.64rem] font-bold uppercase tracking-[0.18em] text-muted-foreground/55"
      >
        {eyebrow}
      </span>
    {/if}
    <span
      class={cn(
        "font-semibold tracking-[-0.03em] text-foreground",
        size === "lg" && "text-[1.55rem] sm:text-[1.7rem]",
        size === "md" && "text-[1.2rem] sm:text-[1.3rem]",
        size === "sm" &&
          "text-[1.3rem] tabular-nums tracking-[-0.04em] sm:text-[1.4rem]",
      )}
    >
      {title}
    </span>

    {#if description}
      <span
        class={cn(
          "mt-2 max-w-[90%] leading-snug text-muted-foreground/70",
          size === "lg" && "text-[0.88rem] sm:text-[0.94rem]",
          size === "md" && "text-[0.78rem] sm:text-[0.82rem]",
          size === "sm" && "text-[0.72rem]",
        )}
      >
        {description}
      </span>
    {/if}

    {#if meta}
      <span
        class="mt-3 text-[0.64rem] font-bold uppercase tracking-[0.13em] text-muted-foreground/45"
      >
        {meta}
      </span>
    {/if}
  </div>

  {#if asideValue}
    <div
      class="absolute right-6 top-1/2 z-10 flex w-[3.25rem] -translate-y-1/2 flex-col items-end sm:right-8"
    >
      <div
        class="w-full whitespace-nowrap text-right text-[2rem] font-semibold leading-none tabular-nums tracking-[-0.045em] text-foreground/90 sm:text-[2.35rem]"
      >
        {asideValue}
      </div>
      {#if asideLabel}
        <div
          class="mt-1 w-full whitespace-nowrap text-right text-[0.62rem] font-bold uppercase tracking-[0.1em] text-muted-foreground/50"
        >
          {asideLabel}
        </div>
      {/if}
    </div>
  {/if}
</button>
