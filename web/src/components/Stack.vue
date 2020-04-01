<template>
    <div class='col col--12 relative'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                mode='stack'
                v-on:mode='emitmode($event)'
            />

            <div class='fr'>
                <button @click='refresh' class='btn fr round btn--stroke btn--gray'>
                    <svg class='icon'><use href='#icon-refresh'/></svg>
                </button>

                <button v-if='complete.includes(stack.status)' @click='deleteStack' class='mr12 btn fr round btn--stroke color-gray color-red-on-hover'>
                    <svg class='icon'><use href='#icon-trash'/></svg>
                </button>
            </div>
        </div>

        <template v-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='!imagery || !imagery.length'>
            <div class='flex-parent flex-parent--center-main py12'>
                No imagery sources found to create a stack with
            </div>
        </template>
        <template v-else-if='stack.status === "None"'>
            <h2 class='w-full align-center txt-h4 py12'>No Stack Deployed</h2>

            <div class='col col--12 py6 border-b border--gray-light'>
                Imagery Source:
            </div>

            <div @click='image = img' :key='img.id' v-for='img in imagery' class='col col--12 grid cursor-pointer bg-darken10-on-hover'>
                <h3 v-if='image.id === img.id' class='px12 py6 txt-h4 w-full bg-gray color-white round' v-text='img.name'></h3>
                <h3 v-else class='txt-h4 round px12 py6' v-text='img.name'></h3>
            </div>

            <div class='col col--12 py6'>
                Inferences List:
            </div>
            <div class='col col--12 py3'>
                <input v-model='inferences' type='text' class='input' placeholder='buildings,schools,roads,...'/>
            </div>

            <div class='flex-parent flex-parent--center-main py12'>
                <button @click='createStack' class='flex-child btn btn--stroke color-gray color-green-on-hover round'>Create Stack</button>
            </div>
        </template>
        <template v-else-if='submit'>
            <div class='flex-parent flex-parent--center-main w-full'>
                <div class='flex-child py24'>Inferences Submitted</div>
            </div>
            <div class='flex-parent flex-parent--center-main w-full'>
                <button @click='submit = false' class='flex-child btn btn--stroke color-gray color-blue-on-hover round'>Close</button>
            </div>
        </template>
        <template v-else-if='complete.includes(stack.status)'>
            <div class='col col--12 grid'>
                <div class='col col--12 grid'>
                    <span v-text='stack.name'/>
                </div>
                <div class='col col--12 pt12 flex-parent flex-parent--center-main'>
                    Imagery Chip Submission
                </div>
                <div class='col col--12'>
                    <TileMap
                        v-on:queue='queue($event)'
                    />
                </div>
            </div>
        </template>
        <template v-else-if='stack.status !== "None"'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
            <div class='flex-parent flex-parent--center-main w-full'>
                <div class='flex-child py24'><span v-text='stack.status'/></div>
            </div>
        </template>
    </div>
</template>

<script>
import TileMap from './TileMap.vue';
import PredictionHeader from './PredictionHeader.vue';

export default {
    name: 'Stack',
    props: ['model', 'prediction', 'imagery'],
    data: function() {
        return {
            complete: [
                'CREATE_COMPLETE',
                'UPDATE_COMPLETE'
            ],
            loading: true,
            looping: false,
            image: '',
            inferences: '',
            submit: false,
            stack: {
                id: false,
                name: '',
                status: 'None'
            }
        };
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getStatus();
        },
        queue: function(geojson) {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack/tiles`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(geojson.geometry)
            }).then((res) => {
                return res.json();
            }).then(() => {
                this.submit = true;
                this.loading = false;
            });
        },
        loop: function() {
            this.looping = true;

            if ([
                'None',
                'CREATE_COMPLETE',
                'UPDATE_COMPLETE',
                'DELETE_COMPLETE'
            ].includes(this.stack.status)) {
                this.looping = false;
                return;
            }

            setTimeout(() => {
                if ([
                    'None',
                    'CREATE_COMPLETE',
                    'UPDATE_COMPLETE',
                    'DELETE_COMPLETE'
                ].includes(this.stack.status)) {
                    this.looping = false;
                    return;
                }

                this.loop();
                this.getStatus();
            }, 5000);
        },
        getStatus: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;

                if (!this.looping) this.loop();
            });
        },
        deleteStack: function() {
            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'DELETE'
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;

                if (!this.looping) this.loop();
            });
        },
        emitmode: function(mode) {
            this.$emit('mode', mode);
        },
        createStack: function() {
            if (!this.image) return;
            if (!this.inferences) return;

            this.loading = true;

            fetch(`${window.location.origin}/v1/model/${this.model.modelId}/prediction/${this.prediction.predictionsId}/stack`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    imagery: this.image.url,
                    inferences: this.inferences
                })
            }).then((res) => {
                return res.json();
            }).then((stack) => {
                this.stack = stack;
                this.loading = false;

                if (!this.looping) this.loop();
            });
        }
    },
    components: {
        PredictionHeader,
        TileMap
    }
}
</script>
