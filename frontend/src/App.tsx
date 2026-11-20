import { Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import MainLayout from './layouts/MainLayout';
import ChatPage from './pages/ChatPage';
import DocumentsPage from './pages/DocumentsPage';
import GuidePage from './pages/GuidePage';
import MemoriesPage from './pages/MemoriesPage';
import NotFoundPage from './pages/NotFoundPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <AppProvider>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<ChatPage />} />
          <Route path="/chat/:conversationId" element={<ChatPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/memories" element={<MemoriesPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/guide" element={<GuidePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </AppProvider>
  );
}
