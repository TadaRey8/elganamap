<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { Splide, SplideSlide, SplideTrack } from "@splidejs/svelte-splide";
    import "@splidejs/splide/css/skyblue";

    /** 画像型 */
    export interface ImgRec {
        image_url: string;
        deleted: string; // "0"|"1"
    }

    /** props */
    export let images: ImgRec[] = [];
    export let msgId: number;
    export let toggleDelete: (id: number, url: string, del: string) => void;

    /* 拡大用モーダルを親に通知 */
    const dispatch = createEventDispatcher<{ open: string }>();
    function open(url: string) {
        dispatch("open", url);
    }
</script>

<!-- サムネイル (1:1)  -->
{#if images.length === 1}
    {#if images[0].deleted === "0"}
        <img
            class="thumb"
            src={images[0].image_url}
            alt="thumb"
            on:click={() => open(images[0].image_url)}
        />
    {:else}
        <div
            class="thumb deleted"
            on:click={() => toggleDelete(msgId, images[0].image_url, "1")}
        >
            非表示
        </div>
    {/if}
{:else}
    <!-- 複数枚: 先頭 + … を重ねて複数あることを示す -->
    {#if images.find((img) => img.deleted === "0") as first}
        <div
            class="multi-thumb"
            role="button"
            tabindex="0"
            on:click={() => open("CAROUSEL")}
        >
            <!-- CAROUSEL sentinel -->
            <img src={first.image_url} alt="thumb" />
            <span class="count">…</span>
        </div>
    {:else}
        <div class="thumb deleted">非表示</div>
    {/if}
{/if}

<!-- モーダル内カルーセル (親ファイルで v-if 制御推奨) -->
<div class="modal-carousel">
    <Splide hasTrack={false} options={splideOpts}>
        <SplideTrack>
            {#each images as img}
                <SplideSlide>…</SplideSlide>
            {/each}
        </SplideTrack>
        <div class="splide__pagination"></div>
    </Splide>
</div>

<style>
    .thumb,
    .multi-thumb {
        width: 96px;
        height: 96px;
        object-fit: cover;
        border-radius: 6px;
        cursor: pointer;
        position: relative;
    }
    .multi-thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 6px;
    }
    .multi-thumb .count {
        position: absolute;
        inset: 0;
        display: grid;
        place-items: center;
        font-size: 2rem;
        color: #fff;
        font-weight: bold;
        background: rgba(0, 0, 0, 0.45);
        border-radius: 6px;
    }
    .deleted {
        display: grid;
        place-items: center;
        background: #eee;
        color: #666;
        font-size: 0.8rem;
        cursor: pointer;
    }
    /* モーダル画像 */
    .modal-carousel {
        max-width: 90vw;
        max-height: 90vh;
    }
    .modal-img {
        max-width: 90vw;
        max-height: 90vh;
        object-fit: contain;
        border-radius: 4px;
    }
</style>
