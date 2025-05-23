<template>
  <v-app id="app">
    <v-app-bar app>
      <nav-bar />
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
    <v-footer app>
      <footer-bar />
    </v-footer>
  </v-app>
</template>

<script>
import NavBar from './components/NavBar.vue';
import FooterBar from './components/FooterBar.vue';

export default {
  name: 'App',
  components: {
    NavBar,
    FooterBar
  }
};
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  /* Vuetify handles margin/padding for v-app */
}

/* Styles for el-header, el-main, el-footer can be removed or adapted for Vuetify components if specific overrides are needed */
/* For example, v-main has its own padding, v-app-bar has its own shadow options via props like 'elevation' */

</style>

