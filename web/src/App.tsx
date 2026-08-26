import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { CommandPage } from './pages/CommandPage';
import { CategoryPage } from './pages/CategoryPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { useTheme } from './hooks/useTheme';

const AppContent: React.FC = () => {
  const { theme } = useTheme();

  return (
    <div className={theme === 'light' ? 'light' : ''}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/commands/:technology/:id" element={<CommandPage />} />
            <Route path="/categories/:technology" element={<CategoryPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <HelmetProvider>
      <AppContent />
    </HelmetProvider>
  );
};

export default App;
