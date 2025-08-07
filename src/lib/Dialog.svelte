<script lang="ts">
  export let visible = false; // 表示／非表示
  export let message = ''; // 本文
  export let onOk: () => void; // 「はい」押下時
  export let onCancel: () => void; // 「いいえ」または × 押下時

  const close = (cb?: () => void) => {
    visible = false;
    cb?.();
  };
</script>

<!-- キー入力をオンにしないとエラーが取れない -->
{#if visible}
  <div class="cd-overlay" role="button" tabindex="0" on:click={() => close(onCancel)}>
    <div class="cd-box" on:click|stopPropagation>
      <p>{message}</p>
      <div class="cd-actions">
        <button class="btn no" on:click={() => close(onCancel)}>いいえ</button>
        <button class="btn yes" on:click={() => close(onOk)}>はい</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .cd-overlay {
    position: fixed;
    inset: 0;
    background: #0007;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
  }
  .cd-box {
    background: #fff;
    padding: 1.5rem 2rem;
    border-radius: 6px;
    min-width: 240px;
    text-align: center;
  }
  .cd-actions {
    margin-top: 1rem;
    display: flex;
    gap: 0.5rem;
    justify-content: center;
  }
  .btn {
    padding: 0.4rem 1rem;
    font-size: 0.9rem;
    width: 80px;
    border-radius: 4px;
    cursor: pointer;
  }
  .btn.yes {
    background: #2b7bfd;
    color: #fff;
    border: none;
  }
  .btn.no {
    background: rgb(255, 255, 255);
    color: #424242;
    border: 1px solid #424242;
  }
</style>
