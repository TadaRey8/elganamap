import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default {
	plugins: [sveltekit()],
	// 開発環境専用のプロキシで、本番では使わない
	// そのままでもデプロイ先で使える
	server: {
		proxy: {
			'/get_locations': { target: 'http://127.0.0.1:5000', changeOrigin: true },
			'/completed': { target: 'http://127.0.0.1:5000', changeOrigin: true },
			'/deleted': { target: 'http://127.0.0.1:5000', changeOrigin: true }
		}
	},
	esbuild: {
		drop: ['console', 'debugger'],
	},
	ssr: {
		noExternal: ['@googlemaps/js-api-loader']
	},

};
