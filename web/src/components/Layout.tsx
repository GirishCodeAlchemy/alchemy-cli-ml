import React from "react";
import Header from "./Header";
import Footer from "./Footer";

interface LayoutProps {
  children: React.ReactNode;
  isDark: boolean;
  onToggleTheme: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, isDark, onToggleTheme }) => {
  return (
    <div className="flex min-h-screen flex-col bg-white dark:bg-navy-950">
      <Header isDark={isDark} onToggleTheme={onToggleTheme} />

      {/* Main content area with top padding for fixed header */}
      <main className="flex-1 pt-16">
        {children}
      </main>

      <Footer />
    </div>
  );
};

export { Layout };
export default Layout;
