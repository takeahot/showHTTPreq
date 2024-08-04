import React, { FC, ReactNode } from 'react';

interface LayoutProps {
  header: ReactNode;
  footer: ReactNode;
  children: ReactNode;
}

const Layout: FC<LayoutProps> = ({ header, footer, children }) => {
  return (
    <div className="layout">
      <header className="layout-header">
        {header}
      </header>
      <main className="layout-content">
        {children}
      </main>
      <footer className="layout-footer">
        {footer}
      </footer>
    </div>
  );
};

export default Layout;
