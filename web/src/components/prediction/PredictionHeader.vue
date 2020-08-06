<template>
    <div class="flex-parent-inline py3">
        <button @click='$router.push({ name: "assets" })' :class='{
            "btn--stroke": mode !== "assets"
        }' class="btn btn--pill btn--pill-stroke btn--s btn--pill-hl round">Assets</button>
        <button @click='$router.push({ name: "stack" })' :class='{
            "btn--stroke": mode !== "stack"
        }' class="btn btn--pill btn--s btn--pill-hc btn--pill-stroke round">Stack</button>
        <button @click='$router.push({ name: "map" })' :class='{
            "btn--stroke": mode !== "map"
        }' class="btn btn--pill btn--s btn--pill-hc btn--pill-stroke round">Map</button>
        <button @click='$router.push({ name: "export" })' :class='{
            "btn--stroke": mode !== "export"
        }' class="btn btn--pill btn--s btn--pill-hc btn--pill-stroke round">Export</button>
        <button @click='$router.push({ name: "retrain" })' :class='{
            "btn--stroke": mode !== "retrain"
        }' class="btn btn--pill btn--s btn--pill-hr btn--pill-stroke round">Retrain</button>
    </div>
</template>

<script>
export default {
    name: 'PredictionHeader',
    props: [],
    data: function() {
        return {
            mode: false
        };
    },
    mounted: function() {
        this.mode = this.$route.path.split('/')[this.$route.path.split('/').length - 1]
    }
}
</script>
