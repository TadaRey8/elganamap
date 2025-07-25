<script lang="ts">
    import { createEventDispatcher } from "svelte";
    export let initial = 0;
    export let label = "値";
    let count: number = initial;

    const dispatch = createEventDispatcher<{ change: { count: number } }>();

    function increment() {
        count += 1;
        dispatch("change", { count });
    }
</script>

<div class="counter">
    <button on:click={increment}>＋1</button>
    <slot>{label}: {count}</slot>
</div>

<style>
    .counter {
        margin: 0.5rem;
        display: inline-block;
    }
    button {
        background: teal;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 4px;
        cursor: pointer;
    }
</style>
