import { Suspense } from 'react';
import {
  createBrowserRouter,
  RouterProvider,
  Outlet,
  Navigate
} from 'react-router-dom';
import { routes } from './routes';
import { RouteGuardComponent } from './guards';
import { RouteConfig } from '../types/router';

// 布局组件
import DefaultLayout from '../layouts/DefaultLayout';
import AuthLayout from '../layouts/AuthLayout';
import MinimalLayout from '../layouts/MinimalLayout';

/**
 * 加载中组件
 */
const LoadingSpinner = () => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
  </div>
);

/**
 * 路由元素创建器 - 包装懒加载和路由守卫
 */
const createRouteElement = (route: RouteConfig) => {
  if (route.redirect) {
    return <Navigate to={route.redirect} replace />;
  }

  if (!route.component) {
    return <Outlet />;
  }

  const Component = route.component;
  const LayoutComponent = getLayoutComponent(route.meta.layout);

  return (
    <LayoutComponent>
      <RouteGuardComponent meta={route.meta} path={route.path}>
        <Suspense fallback={<LoadingSpinner />}>
          <Component />
        </Suspense>
      </RouteGuardComponent>
    </LayoutComponent>
  );
};

/**
 * 获取布局组件
 */
const getLayoutComponent = (layout?: string) => {
  switch (layout) {
    case 'auth':
      return AuthLayout;
    case 'minimal':
      return MinimalLayout;
    default:
      return DefaultLayout;
  }
};

/**
 * 将路由配置转换为 React Router 格式
 */
const transformRoutes = (routeConfigs: RouteConfig[]) => {
  return routeConfigs.map(route => ({
    path: route.path,
    element: createRouteElement(route),
    children: route.children ? transformRoutes(route.children) : undefined
  }));
};

/**
 * 创建路由器实例
 */
export const router = createBrowserRouter(transformRoutes(routes), {
  future: {
    v7_relativeSplatPath: true,
    v7_fetcherPersist: true,
    v7_normalizeFormMethod: true,
    v7_partialHydration: true,
    v7_skipActionErrorRevalidation: true
  }
});

/**
 * 路由器提供者组件
 */
export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;