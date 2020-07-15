<template>
    <div id="app" class='flex-parent flex-parent--center-main relative'>
        <div class='flex-child wmax600 col col--12'>
            <div class='py36 col col--12 grid'>
                <div class='col col--2'></div>
                <div class='col col--8'>
                    <h1 @click='$router.push({ path: "/" })' class='align-center txt-h3 cursor-default txt-underline-on-hover cursor-pointer'>ML Enabler</h1>
                </div>
                <div v-if='!loading.user && $route.path !== "/login"' class='col col--2'>
                    <button v-if='user.name' class='fr btn btn--stroke btn--s round color-gray color-black-on-hover' v-text='user.name'></button>
                    <button v-else @click='$router.push({ path: "/login" })' class='fr btn btn--stroke btn--s round color-gray-light color-gray-on-hover'>Login</button>
                </div>
            </div>

            <template v-if='loading.meta || loading.user'>
                <div class='flex-parent flex-parent--center-main w-full'>
                    <div class='flex-child loading py24'></div>
                </div>
                <div class='flex-parent flex-parent--center-main w-full'>
                    <div class='flex-child py24'>Loading Models</div>
                </div>
            </template>
            <template v-else-if='meta.security === "authenticated" && !user.name && $route.path !== "/login"'>
                <div class='flex-parent flex-parent--center-main pt36'>
                    <svg class='flex-child icon w60 h60 color--gray'><use href='#icon-alert'/></svg>
                </div>

                <div class='flex-parent flex-parent--center-main pt12 pb6'>
                    <h1 class='flex-child txt-h4 cursor-default align-center'>Access Denied</h1>
                </div>
                <div class='flex-parent flex-parent--center-main'>
                    <h2 class='flex-child txt-h5 cursor-default align-center'>Please Login To Access</h2>
                </div>
            </template>
            <template v-else>
                <router-view
                    :meta='meta'
                    :stacks='stacks'
                    @err='err = $event'
                />
            </template>
        </div>

        <Err
            v-if='err'
            :err='err'
            @err='err = $event'
        />
    </div>
</template>

<script>
import Err from './components/Err.vue';

export default {
    name: 'MLEnabler',
    data: function() {
        return {
            err: false,
            user: {
                name: false
            },
            stacks: {
                models: [],
                predictions: [],
                stacks: []
            },
            meta: {
                version: 1,
                environemnt: 'docker',
                security: false
            },
            loading: {
                user: true,
                meta: true
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
            this.getUser();
        },
        external: function(url) {
            if (!url) return;
            window.open(url, "_blank")
        },
        getMeta: function() {
            this.loading.meta = true;
            fetch(window.api + '/v1', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.meta = res;
                this.loading.meta = false;
            }).catch((err) => {
                console.error(err);
            });
        },
        getUser: function() {
            this.loading.user = true;
            fetch(window.api + '/v1/user/self', {
                method: 'GET'
            }).then((res) => {
                return res.json();
            }).then((res) => {
                this.user = res;
                this.loading.user = false;
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
    },
    components: {
        Err
    }
}
</script>
