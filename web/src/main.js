import Vue from 'vue'
import VueRouter from  'vue-router'

import App from './App.vue'

import Home from './components/Home.vue';
import Login from './components/Login.vue';
import Model from './components/Model.vue';
import EditModel from './components/EditModel.vue';
import Prediction from './components/Prediction.vue';

import Assets from './components/prediction/Assets.vue';
import Export  from './components/prediction/Export.vue';
import Map  from './components/prediction/Map.vue';
import Stack from './components/prediction/Stack.vue';
import Retrain from './components/prediction/Retrain.vue';

Vue.use(VueRouter);
Vue.config.productionTip = false

const router = new VueRouter({
    mode: 'hash',
    routes: [
        { path: '/', name: 'home', component: Home },
        { path: '/login', name: 'login', component: Login },

        { path: '/model/new', name: 'newmodel', component: EditModel },
        { path: '/model/:modelid', name: 'model', component: Model },
        { path: '/model/:modelid/edit', name: 'editmodel', component: EditModel },

        {
            name: 'prediction',
            path: '/model/:modelid/prediction/:predid',
            redirect: '/model/:modelid/prediction/:predid/assets',
            component: Prediction,
            children: [{
                name: 'assets',
                path: 'assets',
                component: Assets
            },{
                name: 'stack',
                path: 'stack',
                component: Stack
            },{
                name: 'retrain',
                path: 'retrain',
                component: Retrain
            },{
                name: 'map',
                path: 'map',
                component: Map
            },{
                name: 'export',
                path: 'export',
                component: Export
            }]
        },
    ]
});

window.api = window.location.pathname.replace(/\/admin\/.*/, '');

new Vue({
    router,
    render: h => h(App)
}).$mount('#app')
