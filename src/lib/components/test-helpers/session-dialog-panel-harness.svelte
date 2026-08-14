<script lang="ts">
  import SessionDialogPanel from "$lib/components/session-dialog-panel.svelte";
  import { Dialog } from "$lib/components/ui/dialog";

  type InitialFocusTarget = "primary" | "close";

  interface Props {
    initialFocus?: InitialFocusTarget;
    primaryDisabled?: boolean;
    secondaryDisabled?: boolean;
  }

  let {
    initialFocus = "close",
    primaryDisabled = false,
    secondaryDisabled = false,
  }: Props = $props();

  let open = $state(true);
</script>

<Dialog bind:open>
  <SessionDialogPanel
    title="Confirm Action"
    primaryLabel="Delete"
    {initialFocus}
    {primaryDisabled}
    {secondaryDisabled}
    primaryVariant="destructive"
    onPrimary={() => {}}
    onSecondary={() => {}}
  >
    <p>This action cannot be undone.</p>
  </SessionDialogPanel>
</Dialog>
