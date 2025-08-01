<script lang="ts">
  export let instruction: string | null = null;
  export let status: string | null = null;
  export let msgId!: number;
  export let onOpen: (detail: { msgId: number }) => void = () => {};

  function handleClick() {
    onOpen?.({ msgId });
  }
</script>

<div class="popup">
  <span class="label">案件:</span> <strong>{instruction}</strong><br />
  <span class="label">ステータス:</span> <strong>{status}</strong><br />
  <button class="instruction-btn" on:click={handleClick}> 詳細 </button>
</div>

<style>
  .popup {
    line-height: 1.5;
    font-size: 0.85rem;
  }
  .label {
    color: #666;
  }
</style>
