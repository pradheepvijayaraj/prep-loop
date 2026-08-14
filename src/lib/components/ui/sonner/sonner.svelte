<script lang="ts">
  import {
    Toaster as Sonner,
    type ToasterProps as SonnerProps,
  } from "svelte-sonner";
  import { mode } from "mode-watcher";
  import Loader2Icon from "@lucide/svelte/icons/loader-2";
  import CircleCheckIcon from "@lucide/svelte/icons/circle-check";
  import OctagonXIcon from "@lucide/svelte/icons/octagon-x";
  import InfoIcon from "@lucide/svelte/icons/info";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";

  let { toastOptions = {}, ...restProps }: SonnerProps = $props();

  function mergeClassNames(...values: Array<string | undefined>) {
    return values.filter(Boolean).join(" ");
  }

  const mergedToastOptions = $derived({
    ...toastOptions,
    class: mergeClassNames(toastOptions.class, "cursor-pointer"),
    unstyled: toastOptions.unstyled ?? true,
    classes: {
      ...toastOptions.classes,
      toast: mergeClassNames(
        "relative flex w-[min(22rem,calc(100vw-1.5rem))] min-w-[11rem] items-center gap-2.5 overflow-hidden rounded-md border border-border/55 bg-background/95 px-3.5 py-3 text-foreground shadow-[0_16px_34px_rgba(0,0,0,0.22)] backdrop-blur-xl transition-[border-color,transform,opacity,background-color,box-shadow] duration-150",
        "focus-visible:border-foreground/26 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-foreground/10",
        toastOptions.classes?.toast,
      ),
      content: mergeClassNames("min-w-0 flex-1", toastOptions.classes?.content),
      title: mergeClassNames(
        "text-[0.78rem] leading-snug font-semibold tracking-normal text-foreground/90",
        toastOptions.classes?.title,
      ),
      description: mergeClassNames(
        "mt-0.5 text-[0.82rem] leading-[1.28] tracking-[0.01em] text-muted-foreground/74",
        toastOptions.classes?.description,
      ),
      icon: mergeClassNames(
        "flex h-6 w-6 shrink-0 items-center justify-center text-muted-foreground/78",
        toastOptions.classes?.icon,
      ),
      loader: mergeClassNames(
        "text-muted-foreground/70",
        toastOptions.classes?.loader,
      ),
      actionButton: mergeClassNames(
        "inline-flex h-7 shrink-0 items-center justify-center border border-border/45 bg-transparent px-2.5 text-[0.62rem] font-bold uppercase tracking-[0.12em] text-foreground transition-colors hover:border-foreground/34 hover:bg-muted/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-foreground/10",
        toastOptions.classes?.actionButton,
      ),
      cancelButton: mergeClassNames(
        "inline-flex h-7 shrink-0 items-center justify-center border border-border/32 bg-transparent px-2.5 text-[0.62rem] font-bold uppercase tracking-[0.12em] text-muted-foreground transition-colors hover:border-border/60 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-foreground/10",
        toastOptions.classes?.cancelButton,
      ),
      closeButton: mergeClassNames("hidden", toastOptions.classes?.closeButton),
      success: mergeClassNames(
        "[&_[data-icon]]:text-emerald-600 dark:[&_[data-icon]]:text-emerald-300",
        toastOptions.classes?.success,
      ),
      error: mergeClassNames(
        "[&_[data-icon]]:text-destructive",
        toastOptions.classes?.error,
      ),
      warning: mergeClassNames(
        "[&_[data-icon]]:text-amber-600 dark:[&_[data-icon]]:text-amber-300",
        toastOptions.classes?.warning,
      ),
      info: mergeClassNames(
        "[&_[data-icon]]:text-sky-600 dark:[&_[data-icon]]:text-sky-300",
        toastOptions.classes?.info,
      ),
      loading: mergeClassNames(
        "[&_[data-icon]]:text-muted-foreground/72",
        toastOptions.classes?.loading,
      ),
    },
  });

  function handleToastClick(event: MouseEvent) {
    const target = event.target as HTMLElement | null;
    if (!target) return;

    if (
      target.closest(
        "[data-close-button], [data-button], [data-cancel], [data-action]",
      )
    ) {
      return;
    }

    const toast = target.closest("[data-sonner-toast]");
    if (!(toast instanceof HTMLElement)) return;

    const closeButton = toast.querySelector("[data-close-button]");
    if (closeButton instanceof HTMLButtonElement) {
      closeButton.click();
    }
  }
</script>

<Sonner
  theme={mode.current}
  class="toaster group"
  style="--normal-bg: color-mix(in oklab, var(--color-background) 88%, transparent); --normal-text: var(--color-foreground); --normal-border: color-mix(in oklab, var(--color-border) 82%, transparent);"
  toastOptions={mergedToastOptions}
  onclick={handleToastClick}
  {...restProps}
>
  {#snippet loadingIcon()}
    <Loader2Icon class="size-4 animate-spin text-muted-foreground/74" />
  {/snippet}
  {#snippet successIcon()}
    <CircleCheckIcon class="size-4 text-emerald-600 dark:text-emerald-300" />
  {/snippet}
  {#snippet errorIcon()}
    <OctagonXIcon class="size-4 text-destructive" />
  {/snippet}
  {#snippet infoIcon()}
    <InfoIcon class="size-4 text-sky-600 dark:text-sky-300" />
  {/snippet}
  {#snippet warningIcon()}
    <TriangleAlertIcon class="size-4 text-amber-600 dark:text-amber-300" />
  {/snippet}
</Sonner>
