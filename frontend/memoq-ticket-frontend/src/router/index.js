// import Home from '../views/Home.vue'; // Home.vue 不再作为根路径组件
import Login from '../views/Login.vue';
import TicketSubmit from '../views/TicketSubmit.vue';
import TicketList from '../views/TicketList.vue';
import TicketDetail from '../views/TicketDetail.vue';
import AdminDashboard from '../views/AdminDashboard.vue'; // Main Admin Dashboard
import SupportDashboard from '../views/SupportDashboard.vue';
import UserProfile from '../views/UserProfile.vue';

// New Admin sub-views for company management
import CompanyList from '../views/admin/CompanyList.vue';
import CompanyDetailLayout from '../views/admin/CompanyDetailLayout.vue';
import CompanySSOManagement from '../views/admin/CompanySSOManagement.vue';
import CompanyNotificationTemplateManagement from '../views/admin/CompanyNotificationTemplateManagement.vue';

// New Customer-facing view
import TicketSatisfactionRatingForm from '../views/TicketSatisfactionRatingForm.vue';

// OAuth Callback handler
import OAuthCallback from '../views/OAuthCallback.vue';


const routes = [
  {
    path: '/', // 根路径现在也指向登录页
    name: 'Login', // 可以重命名以区分，或者如果Login是唯一的入口，则可以叫'Login'
    component: Login, // 将 Home 组件替换为 Login 组件
    meta: { title: '登录' } // 更新 meta 信息
  },
  {
    path: '/login', // 保留 /login 路径，也指向 Login 组件，或者可以考虑移除此重复路径，让 / 作为唯一的登录入口
    name: 'Login',
    component: Login,
    meta: { title: '登录' }
  },
  {
    path: '/login/:companySlug',
    name: 'CompanyLogin',
    component: Login,
    props: true,
    meta: { title: '公司登录' }
  },
  {
    path: '/oauth/callback/:platform', 
    name: 'OAuthCallback',
    component: OAuthCallback, 
    props: true,
    meta: { title: 'OAuth处理中...' }
  },
  {
    path: '/submit-ticket/:companyCode?', 
    name: 'TicketSubmit',
    component: TicketSubmit,
    meta: { requiresAuth: true, title: '提交工单' }
  },
  {
    path: '/tickets',
    name: 'TicketList',
    component: TicketList,
    meta: { requiresAuth: true, title: '我的工单' }
  },
  {
    path: '/tickets/:id', 
    name: 'TicketDetail',
    component: TicketDetail,
    props: true,
    meta: { requiresAuth: true, title: '工单详情' }
  },
  {
    path: '/:companySlug/tickets/:ticketId', 
    name: 'CompanyTicketDetail',
    component: TicketDetail, 
    props: true,
    meta: { requiresAuth: true, title: '工单详情' }
  },
  {
    path: '/ticket/:ticketId/rate',
    name: 'TicketSatisfactionRating',
    component: TicketSatisfactionRatingForm,
    props: true,
    meta: { requiresAuth: true, roles: ['customer', 'system_admin'], title: '评价工单' } 
  },
  {
    path: '/admin',
    component: AdminDashboard, 
    meta: { requiresAuth: true, requiresAdmin: true, title: '管理后台' },
    children: [
      {
        path: '', 
        name: 'AdminDashboardDefault',
        redirect: { name: 'AdminCompanyList' } 
      },
      {
        path: 'companies',
        name: 'AdminCompanyList',
        component: CompanyList, 
        meta: { title: '公司管理' }
      },
      {
        path: 'companies/:companyId',
        component: CompanyDetailLayout, 
        props: true,
        meta: { title: '公司详情配置' },
        children: [
          {
            path: '', 
            name: 'AdminCompanyDetailDefault',
            redirect: to => ({ name: 'AdminCompanySSOManagement', params: { companyId: to.params.companyId }})
          },
          {
            path: 'sso',
            name: 'AdminCompanySSOManagement',
            component: CompanySSOManagement,
            props: true,
            meta: { title: 'SSO配置' }
          },
          {
            path: 'notification-templates',
            name: 'AdminCompanyNotificationTemplates',
            component: CompanyNotificationTemplateManagement,
            props: true,
            meta: { title: '通知模板' }
          },
        ]
      },
    ]
  },
  {
    path: '/support',
    name: 'SupportDashboard',
    component: SupportDashboard,
    meta: { requiresAuth: true, requiresSupport: true, title: '技术支持后台' }
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true, title: '个人资料' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'), 
    meta: { title: '页面未找到' }
  }
];

export default routes;
