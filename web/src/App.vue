<template>
    <div id="app" class='flex-parent flex-parent--center-main'>
        <div class='flex-child wmax600 col col--12'>
            <div class='flex-parent flex-parent--center-main py36'>
                <h1 @click='$router.push({ path: "/" })' class='flex-child txt-h3 cursor-default txt-underline-on-hover cursor-pointer'>ML Enabler</h1>
            </div>

            <router-view
                :meta='meta'
                :stacks='stacks'
            />
        </div>
    </div>
</template>

<script>
export default {
    name: 'MLEnabler',
    data: function() {
        return {
            stacks: {
                models: [],
                predictions: [],
                stacks: []
            },
            meta: {
                version: 1,
                environemnt: 'docker'
            }
        }
    },
    mounted: function() {
        this.refresh();
    },
    methods: {
        refresh: function() {
            this.getMeta();
            this.getStacks();
        },
        external: function(url) {
            if (!url) return;
            window.open(url, "_blank")
        },
        getMeta: function() {
            fetch(window.api + '/v1', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.meta = res;
            }).catch((err) => {
                console.error(err);
            });
        },
        getStacks: function() {
            fetch(window.api + '/v1/stacks', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                if (!res.error) {
                    this.stacks = res;
                }
            });
        }
    }
}
</script>
