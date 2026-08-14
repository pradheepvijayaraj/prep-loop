<script lang="ts">
  // Customized primitive: preserve closeOnInteractOutside when regenerating shadcn-svelte components.
  import { Dialog as DialogPrimitive } from "bits-ui";
  import Portal from "../portal.svelte";
  import type { Snippet } from "svelte";
  import * as Dialog from "./index.js";
  import { cn, type WithoutChildrenOrChild } from "$lib/utils.js";
  import type { ComponentProps } from "svelte";
  import { Button } from "$lib/components/ui/button/index.js";
  import XIcon from "@lucide/svelte/icons/x";

  let {
    ref = $bindable(null),
    class: className,
    portalProps,
    children,
    showCloseButton = true,
    closeOnInteractOutside = false,
    ...restProps
  }: WithoutChildrenOrChild<DialogPrimitive.ContentProps> & {
    portalProps?: WithoutChildrenOrChild<ComponentProps<typeof Portal>>;
    children: Snippet;
    showCloseButton?: boolean;
    closeOnInteractOutside?: boolean;
  } = $props();

  function handleInteractOutside(event: Event) {
    if (!closeOnInteractOutside) event.preventDefault();
  }
</script>

<Portal {...portalProps}>
  <Dialog.Overlay />
  <DialogPrimitive.Content
    bind:ref
    data-slot="dialog-content"
    class={cn(
      "bg-background text-foreground data-open:animate-in data-closed:animate-out data-closed:fade-out-0 data-open:fade-in-0 data-closed:zoom-out-[0.985] data-open:zoom-in-[0.985] data-closed:slide-out-to-top-1 data-open:slide-in-from-top-1 border border-border/60 grid max-w-[calc(100%-2rem)] gap-6 p-6 text-sm duration-200 ease-out fixed top-1/2 left-1/2 z-50 w-full -translate-x-1/2 -translate-y-1/2 outline-none",
      className,
    )}
    onInteractOutside={handleInteractOutside}
    {...restProps}
  >
    {@render children?.()}
    {#if showCloseButton}
      <DialogPrimitive.Close data-slot="dialog-close">
        {#snippet child({ props })}
          <Button
            variant="ghost"
            class="absolute top-4 right-4"
            size="icon-sm"
            {...props}
          >
            <XIcon />
            <span class="sr-only">Close</span>
          </Button>
        {/snippet}
      </DialogPrimitive.Close>
    {/if}
  </DialogPrimitive.Content>
</Portal>
