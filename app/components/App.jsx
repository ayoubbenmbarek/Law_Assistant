import React, { useState } from 'react';
import QueryForm from './QueryForm';
import LegalResponse from './LegalResponse';
import './App.css';

// Configuration de l'URL de l'API backend avec détection d'environnement
const getApiBaseUrl = () => {
  // Détection de l'environnement côté client
  if (typeof window !== 'undefined') {
    const isProd = window.location.hostname !== 'localhost' && 
                  !window.location.hostname.includes('127.0.0.1');
    
    if (isProd) {
      return ''; // URL relative en production
    }
    
    // Gestion sécurisée des variables d'environnement
    try {
      return (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) 
        || 'http://localhost:8009';
    } catch (e) {
      return 'http://localhost:8009'; // Fallback
    }
  }
  
  return 'http://localhost:8009';
};

const API_URL = getApiBaseUrl();

const App = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  // This function now receives the response data from QueryForm
  // and doesn't need to make another API call
  const handleSubmit = (responseData) => {
    console.log('Received response data:', responseData);
    setResponse(responseData);
  };

  const handleError = (message) => {
    // S'assurer que handleError reçoit toujours une chaîne de caractères
    if (message === null || message === undefined) {
      setError('Une erreur inconnue est survenue');
      return;
    }
    
    if (typeof message === 'object') {
      try {
        setError(JSON.stringify(message));
      } catch (e) {
        setError('Erreur: Objet non sérialisable');
      }
    } else {
      setError(String(message));
    }
  };

  const resetForm = () => {
    setResponse(null);
    setError(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Assistant Juridique IA</h1>
        <p className="subtitle">Votre conseiller juridique en droit français</p>
      </header>
      
      <main className="app-main">
        {!response ? (
          <div className="query-section">
            <QueryForm 
              onSubmit={handleSubmit} 
              onError={handleError} 
              isLoading={loading}
              setLoading={setLoading}
            />
            
            {error && (
              <div className="error-message">
                <p>{error}</p>
                <button onClick={() => setError(null)}>Réessayer</button>
              </div>
            )}
            
            {loading && (
              <div className="loading-indicator">
                <div className="spinner"></div>
                <p>Recherche en cours dans la base de données juridiques...</p>
              </div>
            )}
          </div>
        ) : (
          <div className="response-section">
            <LegalResponse response={response} />
            <div className="response-actions">
              <button className="button secondary" onClick={resetForm}>
                Nouvelle requête
              </button>
            </div>
          </div>
        )}
      </main>
      
      <footer className="app-footer">
        <p>© 2023 Assistant Juridique IA - Les informations fournies sont à titre indicatif uniquement</p>
      </footer>
    </div>
  );
};

export default App; 