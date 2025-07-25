<script lang="ts">
	// JS／TS どちらでも可
	import { goto } from "$app/navigation"; // ← ボタン遷移用 (任意)
</script>

<main>
	<h1>🎉 こんにちは Svelte!</h1>

	<!-- Aタグだけで OK。SPA 内部遷移になるのでページ全再読込なし -->
	<a href="#/elganamap">マップへリンク</a>

	<!-- クリックでプログラム的に遷移したい場合は goto() -->
	<button on:click={() => goto("./")}>ホームへ戻る(goto)</button>
	<a href="./">ホームへ戻る</a>
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
</style>
