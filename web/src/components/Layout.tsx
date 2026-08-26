import React from "react";
import Header from "./Header";
import Footer from "./Footer";
import { useTheme } from "../hooks/useTheme";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="flex min-h-screen flex-col" style={{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }}>
      <Header isDark={isDark} onToggleTheme={toggleTheme} />
      <main className="flex-1 pt-16">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export { Layout };
export default Layout;
