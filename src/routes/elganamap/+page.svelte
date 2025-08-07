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
  import InfoWindowComponent from '$lib/info-window.svelte';
  import Dialog from '$lib/Dialog.svelte';
  import { mount } from 'svelte';

  let mapElement: HTMLDivElement;
  let map: google.maps.Map;
  let markers: google.maps.marker.AdvancedMarkerElement[][] = [];
  let currentInfoWindow: google.maps.InfoWindow | null = null;
  // ダイアログの変数
  let showDialog = false;
  let dialogMsg = '';
  let dialogOk = () => {};
  let dialogCancel = () => {};
  // フィルターの管理
  let monthOptions: string[] = [];
  let urgencyOptions: string[] = [];
  let statusOptions: string[] = [];
  // ユーザ選択 (初期値 = 全選択で「全件表示」)
  let selectedMonths: Set<string> = new Set();
  let selectedUrgencies: Set<string> = new Set();
  let selectedStatuses: Set<string> = new Set();
  // 画像情報（discovery / before / after 共通）
  let modalImages: ImageRec[] = [];
  let modalIndex = 0;
  let modalMsgId: number | null = null;
  let currentImg: ImageRec | null = null;
  let locations: {
    msg_id: number;
    latitude?: number;
    longitude?: number;
    instruction?: string;
    status?: string;
    urgency?: string;
    customer_info?: string;
    remarks?: string;
    completed?: string | null;
    signal?: string;
    operation_status?: string;
    discovery_images?: ImageRec[];
    before_images?: ImageRec[];
    after_images?: ImageRec[];
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
  const urgencyIndex = (u: string) => (u === '高' ? 0 : u === '中' ? 1 : u === '低' ? 2 : 3);
  const urgencyLabel = (u: string) =>
    u === '高' ? '高' : u === '中' ? '中' : u === '低' ? '低' : 'その他';
  const statusLabel = (s: string | undefined): string =>
    (({ '0': '報告状態', '1': '作業前状態', '2': '作業後状態', '3': '完了状態' }) as const)[
      s ?? ''
    ] ?? '不明';

  // typeで型に名前を定義する
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
    const { Map } = await loader.importLibrary('maps');
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

    locations = await fetchLocations();
    filterMakers(locations);

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

  // get_locations API の呼び出し（非同期処理）
  // 戻り値の型を配列に明示
  async function fetchLocations(): Promise<Location[]> {
    try {
      const res = await fetch(`${API}/get_locations`);
      // 例外が生まれたとき
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // 配列を返す
      return await res.json();
    } catch (err) {
      console.error('get_locations 取得失敗', err);
      // 失敗時は空配列
      return [];
    }
  }

  // マーカーの生成
  function placeMarker(loc: (typeof locations)[number]) {
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
      // マーカーのホバーで出てくる内容（msg_idは消せない）
      title: `${loc.msg_id} (${loc.status})`
    });
    const before = loc.before_images?.[0];
    const after = loc.after_images?.[0];

    // コンポーネントをマウントするためのコンテナを作成
    const container = document.createElement('div');

    // Info-Windowのコンポーネントをマウント
    mount(InfoWindowComponent, {
      target: container,
      props: {
        instruction: loc.instruction ?? '不明',
        status: loc.status ?? '不明',
        msgId: loc.msg_id,
        onOpen: ({ msgId }) => window.dispatchEvent(new CustomEvent('open-acc', { detail: msgId }))
      }
    });
    // InfoWindowを生成
    const iw = new google.maps.InfoWindow({ content: container });

    // マーカークリック時の動作
    marker.addListener('click', () => {
      // 開かれているinfowindowがあれば閉じる
      currentInfoWindow?.close();
      iw.open(map!, marker);
      currentInfoWindow = iw;
      map!.panTo(marker.position as google.maps.LatLng);
    });
    const idx = urgencyIndex(loc.urgency);
    if (!markers[idx]) markers[idx] = [];
    markers[idx].push(marker);
  }
  function clearMarkers() {
    markers.flat().forEach((mk) => (mk.map = null)); // 既存マーカー解除
    markers = [];
  }

  function filterMakers(data: typeof locations) {
    // Set はユニーク集合保持が簡単  :contentReference[oaicite:4]{index=4}
    const monthSet = new Set<string>();
    const urgencySet = new Set<string>();
    const statusSet = new Set<string>();

    data.forEach((loc) => {
      const m = toMonth(loc.instruction);
      if (m) monthSet.add(m);
      urgencySet.add(urgencyLabel(loc.urgency));
      statusSet.add(statusLabel(loc.operation_status));
      placeMarker(loc);
    });

    // UI 反映
    monthOptions = Array.from(monthSet).sort().reverse();
    urgencyOptions = ['高', '中', '低', 'その他'];
    statusOptions = ['報告状態', '作業前状態', '作業後状態', '完了状態'];

    selectedMonths = new Set(monthOptions);
    selectedUrgencies = new Set(urgencyOptions);
    selectedStatuses = new Set(statusOptions);
  }

  // get_locationsから取得した文字列をデコードする関数
  function normalizeStatus(raw: string): string {
    try {
      return decodeURIComponent(raw);
    } catch {
      return raw;
    }
  }

  // 座標が有効かどうかをチェックする関数
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

    // msg_id のハッシュを作って判定
    const visibleIds = new Set(filteredLocations.map((l) => String(l.msg_id)));

    markers.flat().forEach((m) => {
      // title 先頭に埋め込んだ msg_id を “文字列のまま” 取得
      const id = m.title?.split(' ')[0] ?? '';
      if (visibleIds.has(id)) m.map = map;
    });
  }

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

  function toCompleted(v: string | null): '完了済み' | '未完了' {
    return v === null ? '未完了' : '完了済み';
  }

  // フィルター機能の条件
  $: filteredLocations = locations.filter((l) => {
    // チェックボックスが全 OFF の軸は全部除外
    if (selectedMonths.size === 0) return false;
    if (selectedUrgencies.size === 0) return false;
    if (selectedStatuses.size === 0) return false;

    // 各項目ごとの判定
    const m = toMonth(l.instruction); // "YYYY-MM" or null
    const monthHit = m !== null && selectedMonths.has(m);
    const urgencyHit = selectedUrgencies.has(urgencyLabel(l.urgency));
    const statusHit = selectedStatuses.has(statusLabel(l.operation_status));

    // 全項目のAND条件
    return monthHit && urgencyHit && statusHit;
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

  function tryComplete(msgId: number, afterCount: number, btn: HTMLButtonElement) {
    // after_images が 0 枚 → 確認あり
    if (afterCount === 0) {
      dialogMsg = '画像が登録されていませんが、完了しますか？';
      dialogOk = () => completedRegist_on(msgId, btn);
      dialogCancel = () => {}; // 何もしない
      showDialog = true;
      return;
    }
    // 写真がある → 即確認ダイアログ
    dialogMsg = '完了登録を行います。';
    dialogOk = () => completedRegist_on(msgId, btn);
    dialogCancel = () => {};
    showDialog = true;
  }

  // 完了ボタンが押されたら、completedにFalseをセットする
  async function completedRegist_on(msgId: number, btn: HTMLButtonElement) {
    try {
      const res = await fetch(`${API}/completed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ msg_id: msgId })
      });
      if (!res.ok) throw new Error('完了登録に失敗しました');

      console.log('完了登録成功');
      btn.disabled = true; // ボタンを無効化
      btn.textContent = '完了済み';
      btn.classList.add('completed-label');

      locations = await fetchLocations();
      filterMakers(locations);
    } catch (e) {
      console.error('データ取得失敗', e);
      alert(e instanceof Error ? e.message : e);
    }
  }

  // 表示/非表示ボタンが押されたらspot_infoの deleted フラグを立てる
  async function daleteFlg_on(msgId: number, imgUrl: string, deleted: string) {
    try {
      const res = await fetch(`${API}/deleted`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ msg_id: msgId, image_url: imgUrl, deleted })
      });
      if (!res.ok) throw new Error('画像削除に失敗しました');

      modalImages = modalImages.map((img) =>
        img.image_url === imgUrl ? { ...img, deleted: deleted === '1' ? '0' : '1' } : img
      );
      updateCurrentImg(modalIndex);

      locations = await fetchLocations();
      filterMakers(locations);
    } catch (e) {
      console.error('処理失敗', e);
    }
  }

  // 再読み込みボタンが押されたらget_locationsを呼ぶ
  async function reloadLocations() {
    const data = await fetchLocations();
    clearMarkers();
    locations = data;
    filterMakers(locations);
  }
  // モーダルで表示する画像の処理
  function firstVisible(images?: ImageRec[]) {
    const arr = images ?? [];
    return arr.find((img) => img.deleted === '0') ?? null;
  }
  // 表示されている画像の数をカウントする
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

<svelte:head>
  <link rel="stylesheet" href="/manage/css/common.css" />
</svelte:head>

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
            const next = new Set(selectedMonths);
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
            const next = new Set(selectedUrgencies);
            e.currentTarget.checked ? next.add(u) : next.delete(u);
            selectedUrgencies = next;
          }}
        />
        {u}
      </label>
    {/each}
  </details>
  <!-- 進捗フィルター -->
  <details class="filter">
    <summary>進捗状況で絞り込み</summary>
    <label class="all-check">
      <input
        type="checkbox"
        checked={selectedStatuses.size === statusOptions.length}
        on:change={(e) => {
          selectedStatuses = e.currentTarget.checked ? new Set(statusOptions) : new Set();
        }}
      />
      全選択
    </label>
    {#each statusOptions as u}
      <label>
        <input
          type="checkbox"
          checked={selectedStatuses.has(u)}
          on:change={(e) => {
            const next = new Set(selectedStatuses); // ★
            e.currentTarget.checked ? next.add(u) : next.delete(u);
            selectedStatuses = next;
          }}
        />
        {u}
      </label>
    {/each}
  </details>
</div>
<!-- サイドバー -->
<div class="sidebar-wrap">
  <h2 class="sidebar-title">明和町包括的DX地図</h2>
  <aside class="sidebar">
    <!-- (loc.msg_id)←ユニークなキーを設定することで、同一のものを仕分けてくれる -->
    {#each filteredLocations as loc (loc.msg_id)}
      <!-- detailsは折りたたみ要素 -->
      <details class="card" use:register={loc.msg_id}>
        <summary class="header">
          <!-- 受信日時（秒を切り捨て） -->
          <span class="received">{loc.received_at.slice(0, 16)}</span><br />
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
                  <img
                    class="thumb"
                    src={firstVisible(loc.after_images)!.image_url}
                    alt="対応前サムネイル"
                  />
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

            {#if loc.completed === null}
              <button
                class="completed-btn"
                on:click={(e) =>
                  tryComplete(
                    loc.msg_id,
                    loc.after_images?.length ?? 0,
                    e.currentTarget as HTMLButtonElement
                  )}
              >
                この作業を完了する
              </button>
            {:else}
              <span class="completed-label">完了済み</span>
            {/if}
          </p>
        </div>
      </details>
    {/each}
    <!-- サイドバー下部に配置される全クローズボタン -->
    <button class="close-all-btn" on:click={closeAll}> すべてのカードを閉じる </button>
  </aside>
</div>
<!-- モーダル表示 -->
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
          <div class="single-img-frame">
            <img src={modalImages[0].image_url} alt="拡大画像" />
          </div>
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
            drag: true,
            fixedHeight: '80vmin' // 画面短辺の 80%
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
                  <div class="slide-frame">
                    <img src={img.image_url} alt="拡大画像" />
                  </div>
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
<Dialog bind:visible={showDialog} message={dialogMsg} onOk={dialogOk} onCancel={dialogCancel} />

<style>
  /* 外部に出せなかったorz */
  :global(.splide) {
    width: 100%;
    height: 80vmin;
  }

  :global(.splide__track) {
    height: 100%;
  }

  :global(.splide__slide) {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  :global(.splide__arrow) {
    width: 40px;
    height: 40px;
    background: #c0a2f0;
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
  }

  :global(.splide__arrow--prev) {
    left: -56px;
  }

  :global(.splide__arrow--next) {
    right: -56px;
  }

  :global(.splide__pagination) {
    position: relative;
    /* static に戻す */
    bottom: 0;
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
</style>
