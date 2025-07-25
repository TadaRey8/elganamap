import path from 'path';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			// 出力ディレクトリを指定
			pages: 'dist',
			assets: 'dist',
			fallback: 'index.html',
		}),
		alias: {
			$lib: path.resolve('src/lib')
		},
		// SPAモードのための設定
		prerender: {
			entries: []
		},
		paths: {
			base: '/manage'
		},
		router: {
			type: 'hash'
		},
	}
};

export default config;
