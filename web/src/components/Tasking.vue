<template>
    <div class='col col--12 relative'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                mode='tasking'
                v-on:mode='$emit("mode", $event)'
            />
        </div>

        <template v-if='tiles'>
            <div class='col col--12 grid grid--gut12'>
                <h2 class='w-full align-center txt-h4 py12'>Task Creation</h2>

                <div class='col col--12 py6'>
                    <label>Task Name</label>
                    <input type='text' class='input' />
                </div>
                <div class='col col--6 py6'>
                    <label>Tasking Manager URL</label>
                    <input type='text' class='input' />
                </div>
                <div class='col col--6 py6'>
                    <label>Tasking Manager API Token</label>
                    <input type='text' class='input' />
                </div>
                <div class='col col--12 clearfix py6'>
                    <button class='fr btn btn--stroke color-gray color-green-on-hover round'>Create Task</button>
                </div>
            </div>
        </template>
        <template v-else-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else>
            <div class='col col--12 py6'>
                <div class='flex-parent flex-parent--center-main pt36'>
                    <svg class='flex-child icon w60 h60 color-gray'><use href='#icon-info'/></svg>
                </div>

                <div class='flex-parent flex-parent--center-main pt12 pb36'>
                    <h1 class='flex-child txt-h4 cursor-default'>No Inferences Uploaded</h1>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import PredictionHeader from './PredictionHeader.vue';

export default {
    name: 'Tasking',
    props: ['model', 'prediction'],
    data: function() {
        return {
            loading: true,
            tiles: false
        };
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getTilejson();
        },
        getTilejson: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/tiles`, {
                method: 'GET',
                credentials: 'same-origin'
            }).then((res) => {
                if (res.status === 404) {
                    this.tiles = false;
                    this.loading = false;
                } else {
                    res.json().then((tilejson) => {
                        tilejson.tiles[0] = window.location.origin + tilejson.tiles[0];

                        this.loading = false;
                        this.tiles = tilejson;
                    })
                }
            });
        },
    },
    components: {
        PredictionHeader
    }
}
</script>
