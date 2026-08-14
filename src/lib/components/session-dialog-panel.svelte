<script lang="ts">
  import { tick } from "svelte";
  import type { Snippet } from "svelte";
  import { Button, type ButtonVariant } from "$lib/components/ui/button";
  import { DialogContent, DialogTitle } from "$lib/components/ui/dialog";
  import { cn } from "$lib/utils.js";
  import { X } from "@lucide/svelte";

  type InitialFocusTarget = "primary" | "close";

  interface Props {
    title: string;
    primaryLabel: string;
    onPrimary: () => void;
    onSecondary: () => void;
    primaryVariant?: ButtonVariant;
    primaryDisabled?: boolean;
    secondaryDisabled?: boolean;
    secondaryActionLabel?: string;
    onSecondaryAction?: () => void;
    secondaryActionVariant?: ButtonVariant;
    contentClass?: string;
    headerClass?: string;
    dividerClass?: string;
    bodyClass?: string;
    footerClass?: string;
    initialFocus?: InitialFocusTarget;
    children?: Snippet;
  }

  let {
    title,
    primaryLabel,
    onPrimary,
    onSecondary,
    primaryVariant = "default",
    primaryDisabled = false,
    secondaryDisabled = false,
    secondaryActionLabel,
    onSecondaryAction,
    secondaryActionVariant = "outline",
    contentClass,
    headerClass,
    dividerClass,
    bodyClass,
    footerClass,
    initialFocus = "close",
    children,
  }: Props = $props();

  let contentElement = $state<HTMLElement | null>(null);
  let closeButton = $state<HTMLButtonElement | null>(null);
  let primaryButton = $state<HTMLButtonElement | null>(null);

  function isEnabled(element: HTMLButtonElement | null) {
    return !!element && !element.disabled;
  }

  function getInitialFocusTarget() {
    const focusOrder: Record<
      InitialFocusTarget,
      Array<HTMLButtonElement | null>
    > = {
      primary: [primaryButton, closeButton],
      close: [closeButton, primaryButton],
    };

    return (
      (focusOrder[initialFocus] ?? focusOrder.close).find(isEnabled) ?? null
    );
  }

  function handleOpenAutoFocus(event: Event) {
    event.preventDefault();

    void tick().then(() => {
      const target = getInitialFocusTarget();
      if (target) {
        target.focus();
        return;
      }

      contentElement?.focus();
    });
  }
</script>

<DialogContent
  bind:ref={contentElement}
  showCloseButton={false}
  tabindex={-1}
  onOpenAutoFocus={handleOpenAutoFocus}
  class={cn("max-w-[23.5rem] gap-0 p-0", contentClass)}
>
  <div
    class={cn("flex h-14 items-center justify-between gap-3 px-5", headerClass)}
  >
    <DialogTitle class="dialog-title-text">
      {title}
    </DialogTitle>
    <Button
      bind:ref={closeButton}
      variant="ghost"
      size="icon-sm"
      class="rounded-full border border-transparent text-muted-foreground/70 transition-colors hover:border-border hover:text-foreground"
      aria-label="Close dialog"
      onclick={onSecondary}
      disabled={secondaryDisabled}
    >
      <X class="h-4 w-4" />
    </Button>
  </div>

  <div class={cn("mx-5 border-t border-border/70", dividerClass)}></div>

  <div class={cn("px-5 pt-3.5 pb-0 text-foreground", bodyClass)}>
    {@render children?.()}
  </div>

  <div
    class={cn(
      "grid gap-3 px-5 pt-1 pb-4",
      secondaryActionLabel && "grid-cols-2",
      footerClass,
    )}
  >
    <Button
      bind:ref={primaryButton}
      variant={primaryVariant}
      class="ui-button-text h-10 w-full px-4"
      onclick={onPrimary}
      disabled={primaryDisabled}
    >
      {primaryLabel}
    </Button>
    {#if secondaryActionLabel && onSecondaryAction}
      <Button
        variant={secondaryActionVariant}
        class="ui-button-text h-10 w-full px-4"
        onclick={onSecondaryAction}
        disabled={secondaryDisabled}
      >
        {secondaryActionLabel}
      </Button>
    {/if}
  </div>
</DialogContent>
