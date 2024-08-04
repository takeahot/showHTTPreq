import React from 'react';

const Layout = ({ header, footer, children }) => {
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
