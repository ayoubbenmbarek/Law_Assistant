import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import Home from './Home';
import 'tailwindcss/tailwind.css';
import '../styles/globals.css';

// Configuration globale d'Axios
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Intercepteur pour gérer les erreurs d'API de manière globale
axios.interceptors.response.use(
  response => response,
  error => {
    // Gérer les erreurs d'authentification
    if (error.response && error.response.status === 401) {
      // Rediriger vers la page de connexion ou afficher un message
      console.error('Session expirée ou non authentifiée');
    }
    
    // Gérer les erreurs serveur
    if (!error.response) {
      console.error('Erreur de connexion au serveur');
    }
    
    return Promise.reject(error);
  }
);

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-indigo-600 text-white shadow-md">
          <div className="container mx-auto px-4 py-3 flex justify-between items-center">
            <a href="/" className="text-xl font-bold">Assistant Juridique</a>
            <div className="flex space-x-4">
              <a href="/" className="hover:text-indigo-200">Accueil</a>
              <a href="/about" className="hover:text-indigo-200">À propos</a>
            </div>
          </div>
        </nav>
        
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<div className="container mx-auto px-4 py-8">Page À propos</div>} />
            <Route path="*" element={<div className="container mx-auto px-4 py-8">Page non trouvée</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App; 