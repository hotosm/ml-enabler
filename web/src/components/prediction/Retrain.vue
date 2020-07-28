<template>
    <div class='col col--12'>
        <div class='col col--12 border-b border--gray-light clearfix mb6'>
            <PredictionHeader
                v-on:mode='mode = $event'
            />
        </div>
        <template v-if='!prediction || loading.imagery || loading.tasks'>
            <div class='flex-parent flex-parent--center-main w-full py24'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else-if='tasks.length > 0'>
            <div class='col col--12'>
                <h2 class='w-full align-center txt-h4 py12'>Retraining Tasks</h2>

                <div class='col col--12 grid border-b border--gray-light'>
                    <div class='col col--2'>Type</div>
                    <div class='col col--2'>Status</div>
                    <div class='col col--6'>Note</div>
                </div>
                <div :key='task.id' v-for='task in tasks' class='col col--12 grid py6 bg-gray-light-on-hover round'>
                    <div class='col col--2 px6' v-text='task.type'></div>
                    <div class='col col--2 px6' v-text='task.status'></div>
                    <div class='col col--6 px6' v-text='task.statusReason'></div>
                    <div class='col col--2 px6 clearfix'>
                        <button @click='deleteTask(task.id)' class='btn fr round btn--stroke btn--gray color-red-on-hover'>
                            <svg class='icon'><use href='#icon-trash'/></svg>
                        </button>
                    </div>
                </div>
            </div>
        </template>
        <template v-else-if='meta.environment !== "aws"'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    Retraining can only occur when MLEnabler is running in an "aws" environment
                </h1>
            </div>
        </template>
        <template v-else-if='!prediction.modelLink'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    A model must be uploaded before retraining occurs
                </h1>
            </div>
            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <button @click='$router.push({ name: "assets" })' class='flex-child btn btn--stroke round'>
                    Upload Model
                </button>
            </div>
        </template>
        <template v-else-if='!tilejson'>
            <div class='flex-parent flex-parent--center-main pt36'>
                <svg class='flex-child icon w60 h60 color-gray'><use href='#icon-info'/></svg>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default'>No Inferences Uploaded</h1>
            </div>

            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <button @click='$router.push({ name: "stack" })' class='flex-child btn btn--stroke round'>
                    Create Inference Stack
                </button>
            </div>
        </template>
        <template v-else-if='!prediction.checkpointLink'>
            <div class='flex-parent flex-parent--center-main pt12 pb36'>
                <h1 class='flex-child txt-h4 cursor-default align-center'>
                    Checkpoint Upload
                </h1>
            </div>
            <UploadPrediction
                type='checkpoint'
                :prediction='prediction'
                v-on:close='$emit("refresh")'
            />
        </template>
        <template v-else-if='!imagery || !imagery.length'>
            <div class='flex-parent flex-parent--center-main py12'>
                No imagery sources found to create a stack with
            </div>
        </template>
        <template v-else>
            <div class='col col--12'>
                <h2 class='w-full align-center txt-h4 py12'>Model Retraining</h2>

                <label>Imagery Source:</label>
                <div class='border border--gray-light round my12'>
                    <div @click='params.image = img' :key='img.id' v-for='img in imagery' class='col col--12 cursor-pointer bg-darken10-on-hover'>
                        <h3 v-if='params.image.id === img.id' class='px12 py6 txt-h4 w-full bg-gray color-white round' v-text='img.name'></h3>
                        <h3 v-else class='txt-h4 round px12 py6' v-text='img.name'></h3>
                    </div>
                </div>
                <template v-if='!advanced'>
                    <div class='col col--12'>
                        <button @click='advanced = !advanced' class='btn btn--white color-gray px0'><svg class='icon fl my6'><use xlink:href='#icon-chevron-right'/></svg><span class='fl pl6'>Advanced Options</span></button>
                    </div>
                </template>
                <template v-else>
                    <div class='col col--12 border-b border--gray-light mb12'>
                        <button @click='advanced = !advanced' class='btn btn--white color-gray px0'><svg class='icon fl my6'><use xlink:href='#icon-chevron-down'/></svg><span class='fl pl6'>Advanced Options</span></button>
                    </div>
                </template>
                <template v-if='advanced'>
                    <div class='w-full align-center py12'>No Advanced Options Yet</div>
                </template>
                <div class='col col--12 clearfix py12'>
                    <button @click='createRetrain' class='fr btn btn--stroke color-gray color-green-on-hover round'>Retrain</button>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import PredictionHeader from './PredictionHeader.vue';
import UploadPrediction from './UploadPrediction.vue';

export default {
    name: 'Retrain',
    props: ['meta', 'prediction', 'tilejson'],
    data: function() {
        return {
            advanced: false,
            tasks: [],
            imagery: [],
            looping: false,
            params: {
                image: false,
            },
            loading: {
                tasks: true,
                retrain: true,
                imagery: true
            }
        }
    },
    components: {
        UploadPrediction,
        PredictionHeader
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getTasks();
            this.getImagery();
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        getTasks: async function() {
            this.loading.tasks = true;

            try {
                let res = await fetch(window.api + `/v1/task?pred_id=${this.$route.params.predid}&type=retrain`, {
                    method: 'GET'
                });

                let body = await res.json();
                if (!res.ok) throw new Error(body.message)

                this.tasks = body.tasks;
                this.loading.tasks = false;
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
        deleteTask: async function(task_id) {
            try {
                let res = await fetch(window.api + `/v1/task/${task_id}`, {
                    method: 'DELETE'
                });

                let body = await res.json();
                if (!res.ok) throw new Error(body.message)

                this.getTasks()
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
        createRetrain: async function() {
            if (!this.params.image) return;

            try {
                let res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/retrain`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        imagery: this.params.image.url
                    })
                });

                if (!res.ok) {
                    let res = await res.json();
                    throw new Error(res.message)
                }

                this.getTasks();
            } catch (err) {
                console.error(err)
                this.$emit('err', err);
            }
        },
        getImagery: async function() {
            this.loading.imagery = true;

            try {
                let res = await fetch(window.api + `/v1/model/${this.$route.params.modelid}/imagery`, {
                    method: 'GET'
                });

                let body = await res.json();
                if (!res.ok) throw new Error(body.message);

                this.imagery = body;

                this.loading.imagery = false;

                if (this.imagery.length === 1) {
                    this.params.image = this.imagery[0];
                }
            } catch (err) {
                this.$emit('err', err);
            }
        },
    }
}
</script>
