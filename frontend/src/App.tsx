import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AuthModal from './components/auth/AuthModal';

import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Support from './pages/Support';
import LandPrice from './pages/Predictions/LandPrice';
import HousePrice from './pages/Predictions/HousePrice';
import RentalPrice from './pages/Predictions/RentalPrice';
import Askreva from './pages/Askreva';
import AdminPage from './pages/AdminPage';
import LoginPage from './pages/LoginPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        {/* The Modal sits globally above all your routes */}
        <AuthModal />
        
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<LoginPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/support" element={<Support />} />
          <Route path="/askreva" element={<Askreva />} />
          <Route path="/admin" element={<AdminPage />} />
          
          {/* Prediction Routes */}
          <Route path="/land-price" element={<LandPrice />} />
          <Route path="/house-price" element={<HousePrice />} />
          <Route path="/rental-price" element={<RentalPrice />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
