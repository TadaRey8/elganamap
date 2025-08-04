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
  <span class="label">案件:{instruction}</span><br />
  <span class="label">ステータス:{status}</span><br />
  <button class="instruction-btn" on:click={handleClick}> 詳細 </button>
</div>

<style>
  .label {
    font-size: 0.9rem;
    color: #000000;
  }
  .instruction-btn {
    display: block; /* インライン→ブロック */
    margin: auto; /* 中央寄せ */
    margin-top: 10px; /* 上に余白 */
    padding: 4px 10px;
    background: #2b7bfd;
    color: #fff;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
