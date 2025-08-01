<script lang="ts">
  // 環境変数の設定
  import {
    PUBLIC_GOOGLE_MAPS_API_KEY,
    PUBLIC_GOOGLE_MAPS_MAPID,
    PUBLIC_API_BASE
  } from '$env/static/public';
  import { onMount } from 'svelte';
  import { Loader } from '@googlemaps/js-api-loader';
  import { Splide, SplideSlide, SplideTrack } from '@splidejs/svelte-splide';
  import '@splidejs/splide/css';
  // import { Const } from '$lib/const';
  // import { Common } from '$lib/common';
  // ポップアップのコンポーネントのインポート
  import InfoWindow from '$lib/info-window.svelte';

  let mapElement: HTMLDivElement;
  let map: google.maps.Map;
  let markers: google.maps.marker.AdvancedMarkerElement[][] = [[], [], []];
  let currentInfoWindow: google.maps.InfoWindow | null = null;
  // 画像情報（discovery / before / after 共通）
  let modalImages: ImageRec[] = [];
  let modalIndex = 0;
  let modalMsgId: number | null = null;
  let currentImg: ImageRec | null = null;
  let locations: {
    msg_id: number;
    latitude: number;
    longitude: number;
    instruction: string;
    status: string;
    urgency: string;
    customer_info: string;
    remarks: string;
    completed: string | null;
    signal: string;
    discovery_images: ImageRec[];
    before_images: ImageRec[];
    after_images: ImageRec[];
  }[] = [];

  // dev では '', 本番では 'https://…'
  const API = PUBLIC_API_BASE || '';
  // カードのアコーディオンを管理するための辞書型Map
  // constは再代入不可だが、Mapなどリストの内容は変更可能
  const accMap: Map<number, HTMLDetailsElement> = new Map();
  // Google Maps API を Loader で読み込む
  const loader = new Loader({
    apiKey: PUBLIC_GOOGLE_MAPS_API_KEY,
    version: 'weekly',
    region: 'JP',
    language: 'ja',
    libraries: ['marker']
  });
  // マーカーのカスタマイズ
  const urgencyIcon = {
    高: { bg: '#D32F2F', borderColor: '#fff', scale: 1.5, glyph: '高' },
    中: { bg: '#FBC02D', borderColor: '#fff', scale: 1.5, glyph: '中' },
    低: { bg: '#2E7D32', borderColor: '#fff', scale: 1.5, glyph: '低' }
  };
  const urgencyIndex = (u: string) => (u === '高' ? 0 : u === '中' ? 1 : 2);

  type ImageRec = {
    // spot_info
    height?: number;
    width?: number;
    depth?: number;
    cost?: number;
    term?: string;
    image_url: string;
    deleted: string;
    // users
    user_name?: string;
    org?: string;
    email_address?: string;
  };

  // modalIndexが変わる度に発火(リアクティブ宣言)
  $: updateCurrentImg(modalIndex);

  // コンポーネントが最初にDOMにレンダリングされた後に処理が走る
  onMount(async () => {
    const { Map, FeatureType } = await loader.importLibrary('maps');
    const { AdvancedMarkerElement } = await google.maps.importLibrary('marker');

    map = new Map(mapElement, {
      mapId: PUBLIC_GOOGLE_MAPS_MAPID,
      center: { lat: 35.6816858, lng: 139.7466155 },
      zoom: 14,
      gestureHandling: 'greedy',
      restriction: {
        latLngBounds: { north: 46, south: 25, west: 127, east: 150 },
        strictBounds: true
      },
      zoomControl: false,
      fullscreenControl: false,
      streetViewControlOptions: { position: google.maps.ControlPosition.RIGHT_TOP }
    });

    fetch(`${API}/get_locations`)
      .then((r) => r.json())
      .then((data) => {
        locations = data;
        const allMonths = new Set<string>();
        const allUrgencies = new Set<string>();
        locations.forEach((loc) => {
          const m = toMonth(loc.instruction);
          if (m) allMonths.add(m);
          allUrgencies.add(loc.urgency);
          placeMarker(loc);
        });

        monthOptions = Array.from(allMonths).sort().reverse();
        urgencyOptions = ['高', '中', '低'].filter((u) => allUrgencies.has(u));
        selectedMonths = new Set(monthOptions);
        selectedUrgencies = new Set(urgencyOptions);
      })
      .catch((e) => console.error('データ取得失敗', e));

    // カスタムイベント「open-acc」を受け取ってサイドバー開放
    const openAccHandler = (e: Event) => {
      const id = (e as CustomEvent<number>).detail;
      const acc = accMap.get(id);
      if (acc) {
        acc.open = true;
        acc.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };
    window.addEventListener('open-acc', openAccHandler);

    return () => {
      window.removeEventListener('open-acc', openAccHandler);
    };
  });

  // マーカーの生成
  function placeMarker(loc: {
    msg_id: number;
    latitude: number;
    longitude: number;
    instruction: string;
    status: string;
    urgency: string;
    completed: string | null;
    signal: string;
    discovery_images: ImageRec[];
    before_images: ImageRec[];
    after_images: ImageRec[];
  }) {
    if (!map) return;

    if (!isValidCoord(loc.latitude) || !isValidCoord(loc.longitude)) {
      console.log('緯度経度がNullのためスキップ:', loc.msg_id);
      return; // ★ NULL レコードはここで弾く
    }

    const status = normalizeStatus(loc.status);

    // 緊急度がなかった時のマーカースタイル
    const style = urgencyIcon[loc.urgency] ?? {
      bg: '#777',
      borderColor: '#fff',
      glyph: '？',
      scale: 1.5
    };

    const pin = new google.maps.marker.PinElement({
      background: style.bg,
      borderColor: style.borderColor,
      glyph: style.glyph,
      glyphColor: '#fff',
      scale: style.scale
    });

    const marker = new google.maps.marker.AdvancedMarkerElement({
      map,
      position: { lat: loc.latitude, lng: loc.longitude },
      content: pin.element,
      title: `${loc.msg_id} (${loc.status})`
    });
    const before = loc.before_images?.[0];
    const after = loc.after_images?.[0];

    const iw = new google.maps.InfoWindow({
      content: `
			<div class="popup">
				<span class="label">案件:</span> <strong>${loc.instruction ?? '不明'}</strong><br>
				<span class="label">ステータス:</span> <strong>${loc.status ?? '不明'}</strong><br>
				<button class="instruction-btn" data-msg="${loc.msg_id}">
					詳細
				</button>
			</div>
			`
    });
    google.maps.event.addListenerOnce(iw, 'domready', () => {
      // InfoWindow が地図ごとに固有の container を作る
      // そこから msg_id 付きボタンを直接検索
      const sel = `.gm-style-iw button.instruction-btn[data-msg="${loc.msg_id}"]`;
      const btn = document.querySelector(sel) as HTMLButtonElement | null;

      if (btn) {
        btn.addEventListener('click', () => {
          window.dispatchEvent(new CustomEvent('open-acc', { detail: loc.msg_id }));
        });
      }
    });

    marker.addListener('click', () => {
      currentInfoWindow?.close();
      iw.open(map!, marker);
      currentInfoWindow = iw;
      map!.panTo(marker.position as google.maps.LatLng);
    });
    markers[urgencyIndex(loc.urgency)].push(marker);
  }

  // get_locationsから取得した文字列をデコードする関数
  function normalizeStatus(raw: string): string {
    try {
      return decodeURIComponent(raw);
    } catch {
      return raw;
    }
  }

  function isValidCoord(n: unknown): n is number {
    return typeof n === 'number' && !Number.isNaN(n);
  }

  // 先頭の画像が非表示にされた時のサムネイルの処理
  function updateCurrentImg(idx: number) {
    if (!modalImages.length) {
      currentImg = null;
      modalIndex = 0;
      return;
    }
    const norm = ((idx % modalImages.length) + modalImages.length) % modalImages.length;
    modalIndex = norm; // Splide の currentSlide も更新
    currentImg = modalImages[norm];
  }

  $: if (map) {
    // 全部非表示
    markers.flat().forEach((m) => (m.map = null));

    // msg_id のハッシュを作って高速判定
    const visibleIds = new Set(filteredLocations.map((l) => l.msg_id));

    markers.flat().forEach((m) => {
      // title 先頭に埋め込んだ msg_id を “文字列のまま” 取得
      const id = m.title?.split(' ')[0] ?? '';
      if (visibleIds.has(id)) m.map = map;
    });
  }

  // フィルターの管理
  let monthOptions: string[] = [];
  let urgencyOptions: string[] = [];

  // ユーザ選択 (初期値 = 全選択で「全件表示」)
  let selectedMonths: Set<string> = new Set();
  let selectedUrgencies: Set<string> = new Set();

  // 受信 instruction → "YYYY-MM" へ変換
  // フォーマット外なら null を返す
  function toMonth(instr: string | null | undefined): string | null {
    if (typeof instr !== 'string') return null;
    const parts = instr.split('-', 3);
    if (parts.length < 2) return null;
    const [yy, mm] = parts;
    if (!/^\d\d$/.test(yy) || !/^\d\d$/.test(mm)) return null;
    return `20${yy}-${mm}`; // 例: 25-07 → 2025-07
  }

  // 条件に合う配列をリアクティブに計算
  $: filteredLocations = locations.filter((l) => {
    // 月が 1 つも選ばれていない → 全部除外
    if (selectedMonths.size === 0) return false;
    // 緊急度が 1 つも選ばれていない → 全部除外
    if (selectedUrgencies.size === 0) return false;

    // AND 条件
    const m = toMonth(l.instruction);
    const monthHit = m !== null && selectedMonths.has(m);
    const urgencyHit = selectedUrgencies.has(l.urgency);

    return monthHit && urgencyHit;
  });

  // ポップアップの詳細ボタンがクリックされたときの処理
  // Svelteアクションであり、DOMに要素が追加されたタイミングで実行される
  function register(node: HTMLDetailsElement, id: number) {
    accMap.set(id, node); // 生成時に登録
    return {
      destroy() {
        accMap.delete(id); // 要素が消えたら解除
      }
    };
  }

  // 完了ボタンが押されたら、completedにFalseをセットする
  function completedRegist_on(msgId: number, btn: HTMLButtonElement) {
    fetch(`${API}/completed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ msg_id: msgId })
    })
      .then((res) => {
        if (!res.ok) throw new Error('完了登録に失敗しました');
        return res.json();
      })
      .then(() => {
        console.log('完了登録成功');
        btn.disabled = true; // ボタンを無効化
        btn.textContent = '完了済み';
        btn.classList.add('completed-label');
      })
      .catch((err) => {
        console.error('データ取得失敗', err);
        alert(err instanceof Error ? err.message : err);
      });
  }

  // 表示/非表示ボタンが押されたらspot_infoの deleted フラグを立てる
  function daleteFlg_on(msgId: number, imgUrl: string, deleted: string) {
    fetch(`${API}/deleted`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        msg_id: msgId,
        image_url: imgUrl,
        deleted: deleted
      })
    })
      .then((res) => {
        if (!res.ok) throw new Error('画像削除に失敗しました');
        return res.json();
      })
      .then(() => {
        /* ---- 1) フロント側の optimistic update ---- */
        modalImages = modalImages.map((img) =>
          img.image_url === imgUrl ? { ...img, deleted: deleted === '1' ? '0' : '1' } : img
        );
        updateCurrentImg(modalIndex);
        /* ---- 2) サーバー最新を取得して整合 ---- */
        return fetch(`${API}/get_locations`);
      })
      .then((r) => r.json())
      .then((newLocs) => (locations = newLocs))
      .catch((e) => console.error('データ取得失敗', e));
  }

  // 再読み込みボタンが押されたらget_locationsを呼ぶ
  function reloadLocations() {
    fetch(`${API}/get_locations`)
      .then((r) => r.json())
      .then((data) => {
        locations = data;
      })
      .catch((e) => console.error('再読み込み失敗', e));
  }

  function firstVisible(images?: ImageRec[]) {
    const arr = images ?? [];
    return arr.find((img) => img.deleted === '0') ?? null;
  }

  function visibleCount(images?: ImageRec[]) {
    const arr = images ?? [];
    return arr.filter((img) => img.deleted === '0').length;
  }
  // サムネイルをクリックしたら呼ぶ
  function openModal(images: ImageRec[], url: string, id: number) {
    modalImages = images;
    modalMsgId = id;
    const found = images.findIndex((img) => img.image_url === url);
    updateCurrentImg(found >= 0 ? found : 0);
  }
  // モーダル背景を閉じる
  function closeModal() {
    modalImages = [];
    modalMsgId = null;
    modalIndex = 0;
  }

  // すべてのカードを閉じる
  function closeAll() {
    accMap.forEach((el) => (el.open = false));
  }
</script>

<div class="map" bind:this={mapElement}></div>
<button class="reload-btn" on:click={reloadLocations}> 再読み込み </button>
<div class="filter-bar">
  <!-- 月フィルタ -->
  <details class="filter">
    <summary>月で絞り込み</summary>
    <label class="all-check">
      <input
        type="checkbox"
        checked={selectedMonths.size === monthOptions.length}
        on:change={(e) => {
          selectedMonths = e.currentTarget.checked ? new Set(monthOptions) : new Set();
        }}
      />
      全選択
    </label>
    {#each monthOptions as m}
      <label>
        <input
          type="checkbox"
          checked={selectedMonths.has(m)}
          on:change={(e) => {
            const next = new Set(selectedMonths); // ★ 新しい Set を作る
            e.currentTarget.checked ? next.add(m) : next.delete(m);
            selectedMonths = next;
          }}
        />
        {m}
      </label>
    {/each}
  </details>

  <!-- 緊急度フィルタ -->
  <details class="filter">
    <summary>緊急度で絞り込み</summary>
    <label class="all-check">
      <input
        type="checkbox"
        checked={selectedUrgencies.size === urgencyOptions.length}
        on:change={(e) => {
          selectedUrgencies = e.currentTarget.checked ? new Set(urgencyOptions) : new Set();
        }}
      />
      全選択
    </label>
    {#each urgencyOptions as u}
      <label>
        <input
          type="checkbox"
          checked={selectedUrgencies.has(u)}
          on:change={(e) => {
            const next = new Set(selectedUrgencies); // ★
            e.currentTarget.checked ? next.add(u) : next.delete(u);
            selectedUrgencies = next;
          }}
        />
        {u}
      </label>
    {/each}
  </details>
</div>
<div class="sidebar-wrap">
  <h2 class="sidebar-title">明和町包括的DX地図</h2>
  <aside class="sidebar">
    <!-- (loc.msg_id)←ユニークなキーを設定することで、同一のものを仕分けてくれる -->
    {#each filteredLocations as loc (loc.msg_id)}
      <!-- detailsは折りたたみ要素 -->
      <details class="card" use:register={loc.msg_id}>
        <summary class="header">
          <span class="status">{loc.status}</span>
          <span class="msg">{loc.remarks}</span>
        </summary>

        <!-- 展開時に見せる中身 -->
        <div class="body">
          <p class="instruction">
            <span>指示：</span>
            <span class="instruction-text">{loc.instruction}</span>
          </p>
          <!-- 報告（発見）写真 ---------------------------- -->
          <p class="photo-block">
            報告写真：<br />
            {#if loc.discovery_images?.length > 0}
              {#if firstVisible(loc.discovery_images)}
                <span
                  class="thumb-container"
                  role="button"
                  tabindex="0"
                  on:click={() =>
                    openModal(
                      loc.discovery_images,
                      firstVisible(loc.discovery_images)!.image_url,
                      loc.msg_id
                    )}
                  on:keydown={(e) =>
                    openModalKey(
                      e,
                      loc.discovery_images,
                      firstVisible(loc.discovery_images)!.image_url,
                      loc.msg_id
                    )}
                >
                  <img
                    class="thumb"
                    src={firstVisible(loc.discovery_images)!.image_url}
                    alt="報告写真サムネイル"
                  />
                  {#if visibleCount(loc.discovery_images) > 1}
                    <span class="thumb-more">…</span>
                  {/if}
                </span>
              {:else}
                <span
                  class="thumb-container no-image"
                  role="button"
                  tabindex="0"
                  on:click={() => openModal(loc.discovery_images, '', loc.msg_id)}
                  on:keydown={(e) => openModalKey(e, loc.discovery_images, '', loc.msg_id)}
                >
                  非表示
                </span>
              {/if}
            {:else}
              <span class="thumb-container no-image">未登録</span>
            {/if}
          </p>
          <p class="photo-block">
            対応前写真：<br />
            {#if loc.before_images?.length > 0}
              {#if firstVisible(loc.before_images)}
                <span
                  class="thumb-container"
                  role="button"
                  tabindex="0"
                  on:click={() =>
                    openModal(
                      loc.before_images,
                      firstVisible(loc.before_images)!.image_url,
                      loc.msg_id
                    )}
                  on:keydown={(e) =>
                    openModalKey(
                      e,
                      loc.before_images,
                      firstVisible(loc.before_images)!.image_url,
                      loc.msg_id
                    )}
                >
                  <img
                    class="thumb"
                    src={firstVisible(loc.before_images)!.image_url}
                    alt="対応前サムネイル"
                  />
                  {#if visibleCount(loc.before_images) > 1}
                    <span class="thumb-more">…</span>
                  {/if}
                </span>
              {:else}
                <span
                  class="thumb-container no-image"
                  role="button"
                  tabindex="0"
                  on:click={() => openModal(loc.before_images, '', loc.msg_id)}
                  on:keydown={(e) => openModalKey(e, loc.before_images, '', loc.msg_id)}
                >
                  非表示
                </span>
              {/if}
            {:else}
              <span class="thumb-container no-image">未登録</span>
            {/if}
          </p>
          <p class="photo-block">
            対応後写真：<br />
            {#if loc.after_images?.length > 0}
              {#if firstVisible(loc.after_images)}
                <span
                  class="thumb-container"
                  role="button"
                  tabindex="0"
                  on:click={() =>
                    openModal(
                      loc.after_images,
                      firstVisible(loc.after_images)!.image_url,
                      loc.msg_id
                    )}
                  on:keydown={(e) =>
                    openModalKey(
                      e,
                      loc.after_images,
                      firstVisible(loc.after_images)!.image_url,
                      loc.msg_id
                    )}
                >
                  {#if visibleCount(loc.after_images) > 1}
                    <span class="thumb-more">…</span>
                  {/if}
                </span>
              {:else}
                <span
                  class="thumb-container no-image"
                  role="button"
                  tabindex="0"
                  on:click={() => openModal(loc.after_images, '', loc.msg_id)}
                  on:keydown={(e) => openModalKey(e, loc.after_images, '', loc.msg_id)}
                >
                  非表示
                </span>
              {/if}
            {:else}
              <span class="thumb-container no-image">未登録</span>
            {/if}
            {#if loc.after_images?.length > 0}
              {#if loc.completed === null}
                <button
                  class="completed-btn"
                  on:click={(e) =>
                    completedRegist_on(loc.msg_id, e.currentTarget as HTMLButtonElement)}
                >
                  この作業を完了する
                </button>
              {:else}
                <span class="completed-label">完了済み</span>
              {/if}
            {:else}
              <span class="no-work"> 作業未報告</span>
            {/if}
          </p>
        </div>
      </details>
    {/each}
    <!-- サイドバー下部に配置される全クローズボタン -->
    <button class="close-all-btn" on:click={closeAll}> 全クローズ </button>
  </aside>
</div>

{#if modalImages.length}
  <div
    class="modal-overlay"
    role="button"
    tabindex="0"
    on:click={closeModal}
    on:keydown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        closeModal();
      }
    }}
  >
    <div class="modal-content" role="presentation" on:click|stopPropagation>
      <button class="modal-close" on:click={closeModal} aria-label="閉じる">×</button>
      {#if modalImages.length === 1}
        {#if modalImages[0].deleted === '1'}
          <span class="hidden-message">画像は非表示になっています</span>
        {:else}
          <img src={modalImages[0].image_url} alt="拡大画像" />
        {/if}
      {:else}
        <Splide
          hasTrack={false}
          options={{
            type: 'loop',
            role: 'region',
            pagination: true,
            perPage: 1,
            perMove: 1,
            arrows: true,
            drag: true
          }}
          on:move={(e) => updateCurrentImg(e.detail.newIndex)}
          bind:currentSlide={modalIndex}
        >
          <SplideTrack>
            {#each modalImages as img}
              <SplideSlide>
                {#if img.deleted === '1'}
                  <span class="hidden-message">画像は非表示になっています</span>
                {:else}
                  <img src={img.image_url} alt="拡大画像" />
                {/if}
              </SplideSlide>
            {/each}
          </SplideTrack>
          <div class="splide__arrows"></div>
          <div class="splide__pagination"></div>
        </Splide>
      {/if}
    </div>
    <!-- ボタンは常に描画。currentImg が無い瞬間は disabled -->
    <button
      class="modal-delete"
      disabled={!currentImg}
      aria-pressed={currentImg?.deleted === '1'}
      on:click|stopPropagation={() => {
        if (!currentImg) return;
        daleteFlg_on(modalMsgId!, currentImg.image_url, currentImg.deleted);
      }}
    >
      {currentImg?.deleted === '1' ? '表示' : '非表示'}
    </button>
  </div>
{/if}

<style>
  :global(html, body) {
    margin: 0;
    height: 100%;
  }
  :global(.gm-style-iw .popup) {
    font-family: sans-serif;
    font-size: 15px;
    line-height: 1.4;
    color: #333;
  }
  :global(.gm-style-iw .popup .label) {
    font-weight: bold;
    font-size: 13px;
    color: #646464;
  }
  :global(.gm-style-iw .popup .value) {
    font-weight: bold;
    color: #000;
  }

  :global(.gm-style-iw .instruction-btn) {
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
  :global(.splide__arrow) {
    width: 40px;
    height: 40px;
    background: #c0a2f0;
  }
  :global(.splide__arrow--prev) {
    left: -56px;
  }
  :global(.splide__arrow--next) {
    right: -56px;
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
    background: #858484;
    transition: background 1s;
  }
  :global(.splide__pagination__page.is-active) {
    background: #a88af0;
  }
  .map {
    width: 100vw;
    height: 100vh;
  }
  /* 再読み込みボタン */
  .reload-btn {
    position: absolute;
    top: 12px;
    left: 50%; /* 画面中央へ */
    transform: translateX(-50%); /* 中央揃え */
    width: 90px;
    height: 40px;
    border: 1px solid #ccc;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(6px);
    color: #333;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    cursor: pointer;
    user-select: none;
    z-index: 60; /* サイドバー(50)より前面 */
  }
  .reload-btn:active {
    transform: translateX(-50%) scale(0.95);
  }
  .sidebar-wrap {
    position: absolute;
    top: 0;
    right: 0;
    width: 300px;
    height: 100vh; /* 高さマップサイズに合わせる */
    display: flex; /* はみ出さないようにする */
    flex-direction: column; /* 縦に並べる */
  }
  .sidebar {
    flex: 1 1 auto; /* 余った高さを全部使う */
    scrollbar-gutter: stable;
    overflow-y: auto;
    background: rgba(255, 255, 255, 0.9);
    padding: 12px;
  }

  .sidebar-title {
    margin: 0;
    padding: 20px;
    background: #a46cff;
    color: #ffffff;
    font-size: 1.5rem;
    font-weight: bold;
    text-align: center;
  }

  .card {
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    margin-bottom: 6px;
    border: 2px solid #c764f5be;
    border-radius: 3px;
    background: #f7f6f6;
  }

  .card > summary.header {
    justify-content: space-between;
    padding: 10px 10px;
    cursor: pointer;
  }
  .card .body {
    padding: 5px 10px;
    border-top: 1.5px solid #3a3939;
  }
  .instruction-text {
    font-weight: bold;
    color: #000000;
  }
  .completed-btn {
    display: block;
    margin: auto;
    font-size: 15px;
    margin-top: 10px;
    padding: 4px 10px;
    border-radius: 4px;
    background: #ff5656;
    border: none;
    color: #fff;
  }

  .completed-label {
    display: block;
    width: max-content;
    margin: 0 auto;
    padding: 4px 10px;
    background: #9e9e9e;
    border-radius: 18px;
    color: #fff;
    font-size: 1rem;
  }
  .no-work {
    display: block;
    width: max-content;
    margin: 0 auto;
    padding: 4px 10px;
    background: #fdc26a;
    border-radius: 5px;
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 500;
  }
  .thumb-container {
    display: flex;
    margin: auto;
    cursor: pointer;
  }
  .thumb-container.no-image {
    width: 150px;
    height: 150px;
    background: #e0e0e0;
    color: #666;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
  }
  .thumb {
    display: flex;
    margin: auto;
    width: 150px;
    height: 150px;
    object-fit: cover;
    border-radius: 4px;
  }
  .thumb-more {
    display: flex;
    margin: auto;
    margin-left: -20px;
    font-size: 2rem;
  }
  /* モーダル背景 */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100; /* サイドバー・InfoWindow より上 */
  }

  /* モーダル本体 */
  .modal-content {
    position: relative;
    background: #f8f8f8;
    padding: 8px;
    border-radius: 4px;
    max-width: 50vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ×ボタン */
  .modal-close {
    background: transparent;
    border: none;
    font-size: 3rem;
    color: #000000;
    cursor: pointer;
    align-self: flex-end;
  }

  /* 拡大画像 */
  .modal-content img {
    width: auto;
    height: auto;
    max-width: 800px;
    max-height: 600px;
    border-radius: 4px;
    margin: 4px auto 0 auto;
    display: block;
  }
  :global(.splide) {
    width: 100%;
  }
  :global(.splide__slide) {
    display: flex;
    justify-content: center;
    align-items: center;
  }
  :global(.splide__slide img) {
    max-width: 100%;
    max-height: 80vh;
    object-fit: contain;
    margin: auto;
  }
  .modal-delete {
    position: absolute;
    bottom: 8px;
    left: 8px;
    padding: 4px 10px;
    border: none;
    border-radius: 4px;
    background: #ff3939;
    color: #fff;
    cursor: pointer;
  }
  /* ---------- フィルタ UI ---------- */
  .filter-bar {
    position: absolute;
    top: 60px; /* reload-btn より下へ */
    left: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 70;
  }
  .filter {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(6px);
    border: 1px solid #a46cff;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 0.9rem;
  }
  .filter summary {
    cursor: pointer;
    font-weight: 600;
  }
  .filter label {
    display: block;
    margin: 2px 0;
  }
  .all-check {
    border-bottom: 1px solid #ccc;
    margin-bottom: 4px;
    padding-bottom: 2px;
  }
  .close-all-btn {
    flex: 0 0 auto; /* aside の下に固定される (flexbox)  :contentReference[oaicite:2]{index=2} */
    margin: 10px auto; /* 中央寄せ */
    padding: 10px 0;
    width: 100%; /* サイドバー内いっぱい */
    border: none;
    border-radius: 3px;
    background: #c764f5be;
    color: #fff;
    font-weight: 600;
    cursor: pointer;
    user-select: none;
  }
  .close-all-btn:active {
    transform: scale(0.97);
  }

  .status {
    color: #000000;
  }
  .msg {
    color: #000000;
  }
</style>
