<script lang="ts">
    import { Counter } from "$lib";
    let counts = [0, 0];
    let total = counts.reduce((a, b) => a + b, 0);

    function handleChangeAt(idx: number, e: CustomEvent<{ count: number }>) {
        counts[idx] = e.detail.count;
        total = counts.reduce((a, b) => a + b, 0);
    }
</script>

<h1>Counter 合計表示</h1>

<Counter initial={counts[0]} label="A" on:change={(e) => handleChangeAt(0, e)}>
    <span>Aの値: {counts[0]}</span>
</Counter>

<Counter initial={counts[1]} label="B" on:change={(e) => handleChangeAt(1, e)}>
    <span>Bの値: {counts[1]}</span>
</Counter>

<hr />

<p>合計: {total}</p>
