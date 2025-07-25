# 初期設定

## git clone
```bash
git clone <repo-url> elganamap_svelte
cd elganamap_svelte
```

## SvelteKitのインストール
```bash
npm install
```

## 仮想環境の作成
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## ライブラリのインストール
```bash
pip install -r ../requirements.txt
```

## .envの内容
```bash
PUBLIC_GOOGLE_MAPS_API_KEY=xxx
PUBLIC_GOOGLE_MAPS_MAPID=xxx
PUBLIC_API_BASE=http://localhost:5000
```

## 型補完を効かせる

```bash
npm i -D @types/google.maps
```

## `src/global.d.ts`に下記を追加する

```ts
export {};
```

# 実行毎にすること

## バックエンドの実行

```bash
cd elganamap_svelte
source .venv/bin/activate
cd backend
python3 elgana_api.py
```

## フロントエンドの実行

別ターミナルで実行する。
```bash
cd elganamap_svelte
source .venv/bin/activate
npm run dev
```

## アクセス
http://localhost:5173/elganamap へアクセスすると地図が表示される。



# ビルドまでにやったこと

村田さんのdemo-svelteを参考に`svelte.config.ts`と`vite.config.ts`を作成
特に、`vite.config.ts`の方は、APIサーバーのリンクを置く場所がある

`npm i -D @sveltejs/adapter-static`をインストール

`npm run dev`
でテスト

`npm run build`
でビルドする

`explorer.exe .`でエクスプローラーを開く

完成した`dist`ディレクトリの中身をwinSCPで、AWSサーバー上に移す

`https://elganaapi.gaia-fits.com/manage/elganamap`にアクセスする

変更を加える際は、`npm run dev`からやり直す

