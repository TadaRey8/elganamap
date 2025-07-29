<script lang="ts">
    /// <reference types="@sveltejs/kit" />
    import { goto } from "$app/navigation";
</script>

<div class="home">
    <h1>NTTインフラネット 包括的DX地図（検証用）</h1>
</div>

<!-- <a href="#/elganamap" data-sveltekit-prefetch> 包括的DX地図（検証用）へ </a> -->
<button on:click={() => goto(`#/elganamap`)}> 包括的DX地図（検証用） </button>
<button on:click={() => goto(`#/hello`)}> テストページ </button>
<button on:click={() => goto(`#/testCarousel`)}> カルーセルお試し </button>

<style>
    .home {
        text-align: center;
        margin-top: 50px;
    }

    h1 {
        font-size: 2em;
        color: #333;
    }

    button {
        display: block; /* インライン→ブロック */
        margin: auto; /* 中央寄せ */
        margin-top: 10px;
        padding: 10px 20px;
        font-size: 1em;
        background-color: #9c6af8;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }

    button:hover {
        background-color: hsl(261, 96%, 68%);
    }
</style>
