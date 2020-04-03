<template>
    <div class="flex-parent-inline py3">
        <button @click='emit("assets")' :class='{
            "btn--stroke": mode !== "assets"
        }' class="btn btn--pill btn--pill-stroke btn--s btn--pill-hl round">Assets</button>
        <button @click='emit("stack")' :class='{
            "btn--stroke": mode !== "stack"
        }' class="btn btn--pill btn--s btn--pill-hc btn--pill-stroke round">Stack</button>
        <button @click='emit("map")' :class='{
            "btn--stroke": mode !== "map"
        }' class="btn btn--pill btn--s btn--pill-hc btn--pill-stroke round">Map</button>
        <button @click='emit("tasking")' :class='{
            "btn--stroke": mode !== "tasking"
        }' class="btn btn--pill btn--s btn--pill-hr btn--pill-stroke round">Tasking</button>
    </div>
</template>

<script>
export default {
    name: 'PredictionMap',
    props: ['mode'],
    methods: {
        emit: function(mode) {
            this.$emit('mode', mode);
        }
    }
}
</script>
