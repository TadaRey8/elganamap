<script lang="ts">
    import { Splide, SplideSlide, SplideTrack } from "@splidejs/svelte-splide";
    import "@splidejs/splide/css";
    import { onDestroy } from "svelte";

    const images = [
        "/manage/images/Image1.jpg",
        "/manage/images/Image2.jpg",
        "/manage/images/Image3.jpg",
        "/manage/images/Image4.jpg",
    ];

    onDestroy(() => {
        alert("カルーセルページから離れます");
    });
</script>

<main>
    <h1>カルーセルのテストページです。</h1>
    <div class="animals-carousel">
        <Splide
            hasTrack={false}
            options={{
                type: "loop",
                role: "region",
                pagination: true,
                perPage: 1,
                perMove: 1,
                arrows: true,
                drag: true,
            }}
        >
            <SplideTrack>
                {#each images as img}
                    <SplideSlide>
                        <img
                            src={img}
                            alt="スライド画像"
                            style="width:300px;height:300px;object-fit:cover;border-radius:12px"
                            class="slide-image"
                        />
                    </SplideSlide>
                {/each}
            </SplideTrack>

            <!-- 矢印・ドット -->
            <div class="splide__arrows"></div>
            <div class="splide__pagination"></div>
        </Splide>
    </div>

    <a href="./">ホームへ戻る</a>
    <a href="#/">ホームへ戻る(ハッシュルート付き)</a>
</main>

<style>
    main {
        text-align: center;
        margin-top: 3rem;
    }
    a {
        display: block;
        margin: 1rem 0;
        color: #1e88e5;
    }
    .animals-carousel {
        display: block;
        margin: auto;
        width: 50%; /* 横幅を固定 */
        height: 50%; /* 高さを固定 */
    }
    .slide-image {
        width: 300px; /* 横幅を固定 */
        height: 400px; /* 高さを固定 */
        object-fit: cover; /* はみ出し部分をトリミング */
        border-radius: 12px;
    }
    .slide-image:hover {
        cursor: pointer;
    }
    :global(.splide__arrow) {
        width: 50px;
        height: 50px;
        background: #c0a2f0;
    }

    :global(.splide__pagination) {
        position: relative; /* static に戻す */
        bottom: 0;
        margin-top: 1rem;
        justify-content: center;
    }
    :global(.splide__pagination__page) {
        width: 12px;
        height: 12px;
        margin: 0 6px;
        border-radius: 50%;
        background: #d0d0d0;
        transition: background 1s;
    }
    :global(.splide__pagination__page.is-active) {
        background: #a88af0;
    }
</style>
