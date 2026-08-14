<script lang="ts">
  /**
   * Custom scrollbar thumb. Place as a sibling of the scroller inside a
   * `relative overflow-hidden` wrapper that matches the scroller box.
   *
   * Thumb travel is clamped to the track so it never extends above/below
   * the visible frame.
   */
  interface Props {
    scroller: HTMLElement | null;
    /** Horizontal inset from the right edge of the wrapper (px). */
    right?: number;
    /** Vertical inset of the track inside the wrapper (px). */
    insetY?: number;
    /** Optional responsive visual insets for the track. */
    trackInsetTop?: string;
    trackInsetBottom?: string;
    updateTrigger?: unknown;
  }

  let {
    scroller,
    right = 6,
    insetY = 8,
    trackInsetTop = `${insetY}px`,
    trackInsetBottom = `${insetY}px`,
    updateTrigger = undefined,
  }: Props = $props();

  let viewportHeight = $state(0);
  let contentHeight = $state(0);
  let scrollTop = $state(0);
  let isDragging = $state(false);
  let isHovered = $state(false);
  let trackElement = $state<HTMLElement | null>(null);
  let measuredTrackHeight = $state(0);
  let dragStartY = 0;
  let dragStartScrollTop = 0;

  const showScrollbar = $derived(contentHeight > viewportHeight + 1);

  const trackHeight = $derived.by(() => {
    return Math.max(0, measuredTrackHeight || viewportHeight - insetY * 2);
  });

  const thumbHeight = $derived.by(() => {
    if (!showScrollbar || trackHeight <= 0 || contentHeight <= 0) return 0;
    const proportional = (viewportHeight / contentHeight) * trackHeight;
    return Math.min(trackHeight, Math.max(Math.round(proportional), 28));
  });

  const thumbOffset = $derived.by(() => {
    if (!showScrollbar || contentHeight <= viewportHeight || trackHeight <= 0) {
      return 0;
    }
    const scrollRange = contentHeight - viewportHeight;
    const thumbRange = trackHeight - thumbHeight;
    if (scrollRange <= 0 || thumbRange <= 0) return 0;
    const raw = (scrollTop / scrollRange) * thumbRange;
    // Hard clamp — never paint above or below the track
    return Math.max(0, Math.min(thumbRange, Math.round(raw)));
  });

  function updateMetrics() {
    if (!scroller) {
      viewportHeight = 0;
      contentHeight = 0;
      scrollTop = 0;
      return;
    }
    viewportHeight = scroller.clientHeight;
    contentHeight = scroller.scrollHeight;
    measuredTrackHeight = trackElement?.clientHeight ?? 0;
    // Clamp scrollTop for measurement (overscroll can go negative/beyond)
    const maxScroll = Math.max(0, contentHeight - viewportHeight);
    scrollTop = Math.max(0, Math.min(maxScroll, scroller.scrollTop));
  }

  function scheduleUpdate() {
    requestAnimationFrame(updateMetrics);
  }

  function beginDrag(event: PointerEvent) {
    if (!scroller || !showScrollbar || thumbHeight <= 0) return;
    event.preventDefault();
    isDragging = true;
    dragStartY = event.clientY;
    dragStartScrollTop = scroller.scrollTop;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  function drag(event: PointerEvent) {
    if (!isDragging || !scroller) return;
    const scrollRange = contentHeight - viewportHeight;
    const thumbRange = trackHeight - thumbHeight;
    if (scrollRange <= 0 || thumbRange <= 0) return;
    const nextScrollTop =
      dragStartScrollTop +
      ((event.clientY - dragStartY) / thumbRange) * scrollRange;
    scroller.scrollTop = Math.max(0, Math.min(scrollRange, nextScrollTop));
  }

  function endDrag(event?: PointerEvent) {
    if (!isDragging) return;
    isDragging = false;
    if (
      event?.currentTarget instanceof HTMLElement &&
      event.currentTarget.hasPointerCapture(event.pointerId)
    ) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  function nudgeScroll(event: KeyboardEvent) {
    if (!scroller) return;
    const amount = Math.max(24, viewportHeight * 0.12);
    let nextScrollTop: number | null = null;
    switch (event.key) {
      case "ArrowUp":
        nextScrollTop = scroller.scrollTop - amount;
        break;
      case "ArrowDown":
        nextScrollTop = scroller.scrollTop + amount;
        break;
      case "PageUp":
        nextScrollTop = scroller.scrollTop - viewportHeight;
        break;
      case "PageDown":
        nextScrollTop = scroller.scrollTop + viewportHeight;
        break;
      case "Home":
        nextScrollTop = 0;
        break;
      case "End":
        nextScrollTop = contentHeight - viewportHeight;
        break;
    }
    if (nextScrollTop === null) return;
    event.preventDefault();
    scroller.scrollTop = Math.max(
      0,
      Math.min(contentHeight - viewportHeight, nextScrollTop),
    );
  }

  $effect(() => {
    const el = scroller;
    if (!el) {
      viewportHeight = 0;
      contentHeight = 0;
      scrollTop = 0;
      return;
    }

    const onScroll = () => updateMetrics();
    const observer = new ResizeObserver(scheduleUpdate);
    const mutationObserver = new MutationObserver(scheduleUpdate);

    el.addEventListener("scroll", onScroll, { passive: true });
    observer.observe(el);
    if (trackElement) observer.observe(trackElement);
    for (const child of Array.from(el.children)) {
      if (child instanceof Element) observer.observe(child);
    }
    mutationObserver.observe(el, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    scheduleUpdate();
    const t1 = window.setTimeout(scheduleUpdate, 50);
    const t2 = window.setTimeout(scheduleUpdate, 250);

    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
      el.removeEventListener("scroll", onScroll);
      observer.disconnect();
      mutationObserver.disconnect();
    };
  });

  $effect(() => {
    updateTrigger;
    scheduleUpdate();
  });
</script>

{#if showScrollbar && thumbHeight > 0 && trackHeight > 0}
  <div
    class="pointer-events-none absolute z-50"
    bind:this={trackElement}
    style={`top: ${trackInsetTop}; bottom: ${trackInsetBottom}; right: ${right - 5}px; width: 13px;`}
  >
    <button
      type="button"
      class={`group pointer-events-auto absolute left-0 top-0 flex w-full touch-none items-start justify-center rounded-full p-0 outline-none ${isHovered || isDragging ? "bg-foreground/10" : ""}`}
      style={`height: ${thumbHeight}px; transform: translate3d(0, ${thumbOffset}px, 0); will-change: transform;`}
      tabindex="0"
      aria-label="Scroll content"
      onpointerenter={() => (isHovered = true)}
      onpointerleave={() => (isHovered = false)}
      onpointerdown={beginDrag}
      onpointermove={drag}
      onpointerup={endDrag}
      onpointercancel={endDrag}
      onkeydown={nudgeScroll}
    >
      <span
        class="mt-0.5 h-[calc(100%-0.25rem)] w-[3px] rounded-full bg-foreground/30 transition-[width,background-color] duration-150 group-hover:w-[5px] group-hover:bg-foreground/65 group-active:bg-foreground/80"
      ></span>
    </button>
  </div>
{/if}
