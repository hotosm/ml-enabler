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
                    <div class='flex-child py24'>Loading MLEnabler</div>
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
                    @auth='refresh'
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
                environment: 'docker',
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
        refresh: async function() {
            await this.getMeta();
            await this.getUser();
            this.getStacks();
        },
        external: function(url) {
            if (!url) return;
            window.open(url, "_blank")
        },
        getMeta: async function() {
            try {
                this.loading.meta = true;
                const res = await fetch(window.api + '/v1/meta', {
                    method: 'GET'
                });
                const body = await res.json();
                this.loading.meta = false;
                if (!res.ok) throw new Error(body.message);
                this.meta = body;
            } catch (err) {
                this.err = err;
            }
        },
        getUser: async function() {
            try {
                this.loading.user = true;
                let res = await fetch(window.api + '/v1/user/self', {
                    method: 'GET'
                });

                this.loading.user = false;
                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.user = body;
            } catch (err) {
                console.error(err);
            }
        },
        getStacks: async function() {
            try {
                let res = await fetch(window.api + '/v1/stacks', {
                    method: 'GET'
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);
                this.stacks = body;
            } catch(err) {
                console.error(err);
            }
        }
    },
    components: {
        Err
    }
}
</script>
