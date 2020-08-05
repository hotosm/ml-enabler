<template>
    <div class='col col--12 grid pt12'>
        <template v-if='loading'>
            <div class='flex-parent flex-parent--center-main w-full'>
                <div class='flex-child loading py24'></div>
            </div>
        </template>
        <template v-else>
            <div class='col col--12 flex-parent flex-parent--center-main'>
                <h3 class='flex-child txt-h4 py6'>Login</h3>
            </div>

            <div class='col col--12 flex-parent flex-parent--center-main'>
                <div class='w240 col col--12 grid grid--gut12'>
                    <label class='mt12'>Username:</label>
                    <input v-on:keyup.enter='login' :class='{
                         "input--border-red": attempted && !username
                    }' v-model='username' type='text' class='input'/>

                    <label class='mt12'>Password:</label>
                    <input v-on:keyup.enter='login' :class='{
                         "input--border-red": attempted && !password
                   } ' v-model='password' type='password' class='input'/>

                    <button @click='login' class='mt12 w-full color-gray color-green-on-hover btn btn--stroke round'>Login</button>
                </div>
            </div>

        </template>
    </div>
</template>

<script>
export default {
    name: 'Login',
    props: ['meta'],
    data: function() {
        return {
            loading: false,
            attempted: false,
            username: '',
            password: ''
        }
    },
    methods: {
        close: function() {
            this.$emit('close');
        },
        external: function(url) {
            if (!url) return;

            window.open(url, "_blank")
        },
        login: async function() {
            this.attempted = true;

            if (!this.username.length) return;
            if (!this.password.length) return;
            this.loading = true;

            try {
                const res = await fetch(window.api + `/v1/user/login`, {
                    method: 'post',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        username: this.username,
                        password: this.password
                    })
                });

                const body = await res.json();
                if (!res.ok) throw new Error(body.message);

                this.loading = false;

                this.$emit('auth');
                this.$router.push('/')
            } catch (err) {
                this.$emit('err', err);
            }
        }
    }
}
</script>
