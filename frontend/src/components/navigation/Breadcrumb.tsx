import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { getBreadcrumb } from '../../router/routes';

/**
 * 面包屑导航组件
 */
const Breadcrumb: React.FC = () => {
  const location = useLocation();
  const breadcrumbItems = getBreadcrumb(location.pathname);

  // 如果只有一个项目且为首页，不显示面包屑
  if (breadcrumbItems.length === 1 && breadcrumbItems[0].path === '/') {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 bg-white px-4 py-3 rounded-lg shadow-sm">
      {breadcrumbItems.map((item, index) => {
        const isLast = index === breadcrumbItems.length - 1;
        const isHome = item.path === '/';

        return (
          <React.Fragment key={`${item.path}-${index}`}>
            {/* 分隔符 */}
            {index > 0 && (
              <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
            )}

            {/* 面包屑项 */}
            <div className="flex items-center">
              {isHome && <Home className="h-4 w-4 mr-1 flex-shrink-0" />}

              {isLast || !item.path ? (
                <span className="text-gray-900 font-medium truncate">
                  {item.label}
                </span>
              ) : (
                <Link
                  to={item.path}
                  className="text-gray-600 hover:text-gray-900 hover:underline transition-colors truncate"
                >
                  {item.label}
                </Link>
              )}
            </div>
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default Breadcrumb;