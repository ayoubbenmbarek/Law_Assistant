import React, { useState } from 'react';
import './LegalSearch.css';

// Get API URL from App component's logic
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

const LegalSearch = () => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState('semantic');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResults([]);
    
    try {
      let endpoint;
      
      switch(searchType) {
        case 'codes':
          endpoint = `${API_URL}/api/search/codes?q=${encodeURIComponent(query)}&limit=10`;
          break;
        case 'jurisprudence':
          endpoint = `${API_URL}/api/search/jurisprudence?q=${encodeURIComponent(query)}&limit=10`;
          break;
        case 'conseil':
          endpoint = `${API_URL}/api/search/conseil?q=${encodeURIComponent(query)}&limit=10`;
          break;
        case 'semantic':
        default:
          endpoint = `${API_URL}/api/search/semantic?q=${encodeURIComponent(query)}&limit=10`;
          break;
      }
      
      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Format results based on the search type
      let formattedResults = [];
      
      if (searchType === 'semantic') {
        formattedResults = data;
      } else if (searchType === 'codes' || searchType === 'jurisprudence' || searchType === 'conseil') {
        // Adjust based on your API response structure
        formattedResults = data.results || [];
      }
      
      setResults(formattedResults);
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Une erreur s\'est produite lors de la recherche');
    } finally {
      setIsLoading(false);
    }
  };

  const viewResultDetails = (result) => {
    setSelectedResult(result);
  };

  const closeDetails = () => {
    setSelectedResult(null);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Date inconnue';
    
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    } catch (e) {
      return dateString;
    }
  };

  const truncateText = (text, maxLength = 300) => {
    if (!text) return '';
    return text.length <= maxLength 
      ? text 
      : text.substring(0, maxLength) + '...';
  };

  return (
    <div className="legal-search-container">
      <h2 className="search-title">Recherche dans la base juridique</h2>
      
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-inputs">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher dans les textes juridiques..."
            className="search-query-input"
          />
          
          <select 
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            className="search-type-select"
          >
            <option value="semantic">Recherche sémantique</option>
            <option value="codes">Codes</option>
            <option value="jurisprudence">Jurisprudence</option>
            <option value="conseil">Conseil d'État</option>
          </select>
          
          <button type="submit" className="search-button" disabled={isLoading}>
            {isLoading ? 'Recherche...' : 'Rechercher'}
          </button>
        </div>
      </form>
      
      {isLoading && (
        <div className="loading-indicator">
          <div className="spinner"></div>
          <p>Recherche en cours dans la base de données juridiques...</p>
        </div>
      )}
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Réessayer</button>
        </div>
      )}
      
      {!isLoading && !error && results.length === 0 && query && (
        <div className="no-results">
          <p>Aucun résultat trouvé pour "{query}"</p>
        </div>
      )}
      
      {!isLoading && !error && results.length > 0 && !selectedResult && (
        <div className="search-results">
          <h3>Résultats ({results.length})</h3>
          
          <div className="results-list">
            {results.map((result, index) => (
              <div key={index} className="result-card">
                <h4>{result.title || 'Texte juridique'}</h4>
                
                {result.score && (
                  <div className="result-score">
                    Pertinence: {Math.round(result.score * 100)}%
                  </div>
                )}
                
                <div className="result-metadata">
                  <span className="result-type">{result.type || result.jurisdiction || 'Document juridique'}</span>
                  {result.date && <span className="result-date">• {formatDate(result.date)}</span>}
                </div>
                
                {result.metadata && result.metadata.summary && (
                  <div className="result-summary">
                    <p>{result.metadata.summary}</p>
                  </div>
                )}
                
                <div className="result-content">
                  <p>{truncateText(result.content || result.text || '')}</p>
                </div>
                
                <button 
                  className="view-details-button"
                  onClick={() => viewResultDetails(result)}
                >
                  Voir les détails
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {selectedResult && (
        <div className="result-details">
          <button className="close-button" onClick={closeDetails}>
            &times; Retour aux résultats
          </button>
          
          <h3>{selectedResult.title || 'Texte juridique'}</h3>
          
          <div className="details-metadata">
            <div className="metadata-item">
              <strong>Type:</strong> {selectedResult.type || selectedResult.jurisdiction || 'Document juridique'}
            </div>
            
            {selectedResult.date && (
              <div className="metadata-item">
                <strong>Date:</strong> {formatDate(selectedResult.date)}
              </div>
            )}
            
            {selectedResult.number && (
              <div className="metadata-item">
                <strong>Numéro:</strong> {selectedResult.number}
              </div>
            )}
            
            {selectedResult.chamber && (
              <div className="metadata-item">
                <strong>Chambre:</strong> {selectedResult.chamber}
              </div>
            )}
            
            {selectedResult.solution && (
              <div className="metadata-item">
                <strong>Solution:</strong> {selectedResult.solution}
              </div>
            )}
          </div>
          
          {selectedResult.metadata && selectedResult.metadata.summary && (
            <div className="details-summary">
              <h4>Résumé</h4>
              <p>{selectedResult.metadata.summary}</p>
            </div>
          )}
          
          <div className="details-content">
            <h4>Contenu</h4>
            <div className="legal-text">
              {(selectedResult.content || selectedResult.text || '')
                .split('\n')
                .map((line, i) => <p key={i}>{line}</p>)
              }
            </div>
          </div>
          
          {selectedResult.url && (
            <div className="details-links">
              <a 
                href={selectedResult.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="external-link"
              >
                Voir le document original
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LegalSearch; 