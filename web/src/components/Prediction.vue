<template>
    <div class="col col--12">
        <div class='col col--12 clearfix py6'>
            <h2 class='fl cursor-default' v-text='"Prediction: " + prediction.version'></h2>

            <button @click='$router.push({ name: "model", params: { modelid: $route.params.modelid } })' class='btn fr round btn--stroke color-gray color-black-on-hover'>
                <svg class='icon'><use href='#icon-close'/></svg>
            </button>

            <span class='fr mr6 bg-blue-faint bg-blue-on-hover color-white-on-hover color-blue inline-block px6 py3 round txt-xs txt-bold cursor-pointer' v-text='"id: " + prediction.predictionsId'/>
        </div>
        <div class='border border--gray-light round col col--12 px12 py12 clearfix'>
            <router-view
                :meta='meta'
                :prediction='prediction'
                :tilejson='tilejson'
                @refresh='refresh'
            />
        </div>
    </div>
</template>

<script>
export default {
    name: 'Prediction',
    props: ['meta'],
    data: function() {
        return {
            mode: 'assets',
            prediction: {},
            tilejson: false
        }
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        ecrLink(ecr) {
            const url = `https://console.aws.amazon.com/ecr/repositories/${ecr.split(':')[0]}/`;
            this.external(url);
        },
        logLink: function(stream) {
            const url = `https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/%252Faws%252Fbatch%252Fjob/log-events/${encodeURIComponent(stream)}`
            this.external(url);
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        refresh: function() {
            this.getTilejson();
            this.getPrediction();
        },
        getPrediction: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}`, {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.prediction = res;
            });
        },
        getTilejson: function() {
            fetch(window.api + `/v1/model/${this.$route.params.modelid}/prediction/${this.$route.params.predid}/tiles`, {
                method: 'GET',
                credentials: 'same-origin'
            }).then((res) => {
                if (res.status === 404) {
                    this.tilejson = false;
                } else {
                    res.json().then((tilejson) => {
                        tilejson.tiles[0] = window.location.origin + window.api + tilejson.tiles[0];

                        this.tilejson = tilejson;
                    })
                }
            });
        }
    }
}
</script>
