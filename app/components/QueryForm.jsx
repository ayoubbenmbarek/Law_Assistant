import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './QueryForm.css';

// Configuration d'axios avec détection automatique de l'environnement
const getApiBaseUrl = () => {
  // Vérifier si window.location est disponible (navigateur)
  if (typeof window !== 'undefined') {
    // Détecter si nous sommes en production en vérifiant l'URL
    const isProd = window.location.hostname !== 'localhost' && 
                  !window.location.hostname.includes('127.0.0.1');
    
    if (isProd) {
      return ''; // URL relative en production
    }
    
    // En développement, utiliser l'URL de l'API de développement
    // Utiliser une valeur par défaut si REACT_APP_API_URL n'est pas défini
    try {
      return (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) 
        || 'http://localhost:8009';
    } catch (e) {
      return 'http://localhost:8009'; // Fallback
    }
  }
  
  // Fallback pour SSR ou environnements sans window
  return 'http://localhost:8009';
};

const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000, // timeout de 30 secondes
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * QueryForm component for legal questions
 * 
 * This component provides a form for users to submit legal questions,
 * with options for specifying the domain and additional context.
 */
const QueryForm = ({ onSubmit, onError = () => {}, isLoading = false, setLoading = () => {} }) => {
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [domain, setDomain] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [domains, setDomains] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);
  const [selectedDocType, setSelectedDocType] = useState('');
  const [showSources, setShowSources] = useState(false);
  const [sources, setSources] = useState([]);
  const [isSearchingSources, setIsSearchingSources] = useState(false);

  // Charger les domaines et types de documents au chargement du composant
  useEffect(() => {
    const fetchDomains = async () => {
      try {
        const response = await api.get('/api/sources/domains');
        setDomains(response.data);
      } catch (error) {
        console.error('Erreur lors du chargement des domaines:', error);
      }
    };

    const fetchDocumentTypes = async () => {
      try {
        const response = await api.get('/api/sources/types');
        setDocumentTypes(response.data);
      } catch (error) {
        console.error('Erreur lors du chargement des types de documents:', error);
      }
    };

    fetchDomains();
    fetchDocumentTypes();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      if (typeof onError === 'function') {
        onError('Veuillez saisir une question.');
      }
      return;
    }
    
    // Ensure query is at least 10 characters
    if (query.trim().length < 10) {
      if (typeof onError === 'function') {
        onError('Votre question doit contenir au moins 10 caractères.');
      }
      return;
    }
    
    setIsSubmitting(true);
    setLoading(true); // Set loading state in parent component
    
    try {
      console.log('Sending query to API:', {
        query,
        domain: domain || undefined,
        context: context || undefined
      });
      
      const response = await api.post('/api/query/query', {
        query: query,
        domain: domain || undefined,
        context: context || undefined
      });
      
      console.log('Received response:', response.data);
      
      if (typeof onSubmit === 'function') {
        onSubmit(response.data);
      }
    } catch (error) {
      console.error('Erreur lors de la soumission de la requête:', error);
      
      // Enhanced error handling to show validation errors clearly
      let errorMessage = 'Une erreur est survenue lors du traitement de votre requête.';
      
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        if (error.response.status === 422 && error.response.data && error.response.data.detail) {
          // Handle FastAPI validation errors
          if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail
              .map(err => `${err.loc.join('.')} - ${err.msg}`)
              .join('; ');
          } else {
            errorMessage = error.response.data.detail;
          }
        } else {
          errorMessage = error.response.data?.detail || `Error ${error.response.status}: ${error.response.statusText}`;
        }
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'Aucune réponse reçue du serveur. Vérifiez votre connexion internet.';
      }
      
      if (typeof onError === 'function') {
        onError(errorMessage);
      }
    } finally {
      setIsSubmitting(false);
      setLoading(false); // Set loading state in parent component
    }
  };

  const searchSources = async () => {
    if (!query.trim()) {
      if (typeof onError === 'function') {
        onError('Veuillez saisir un terme de recherche.');
      }
      return;
    }
    
    setIsSearchingSources(true);
    setSources([]);
    
    try {
      const response = await api.get('/api/sources/search', {
        params: {
          query: query,
          limit: 10,
          doc_type: selectedDocType || undefined
        }
      });
      
      setSources(response.data);
      setShowSources(true);
    } catch (error) {
      console.error('Erreur lors de la recherche de sources:', error);
      if (typeof onError === 'function') {
        onError(error.response?.data?.detail || 'Une erreur est survenue lors de la recherche de sources.');
      }
    } finally {
      setIsSearchingSources(false);
    }
  };

  const selectSource = (source) => {
    const sourceContext = `Selon ${source.title} (${source.date}): "${source.content.substring(0, 300)}..."`;
    setContext(previousContext => {
      if (previousContext) {
        return `${previousContext}\n\n${sourceContext}`;
      }
      return sourceContext;
    });
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Posez votre question juridique</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-1">
            Votre question
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex: Quelles sont les conditions pour créer une SAS en France?"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            rows="3"
            required
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label htmlFor="domain" className="block text-sm font-medium text-gray-700">
              Domaine juridique
            </label>
            <span className="text-xs text-gray-500">(Optionnel)</span>
          </div>
          <select
            id="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">Tous les domaines</option>
            {domains.map((domain) => (
              <option key={domain} value={domain}>
                {domain}
              </option>
            ))}
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <button 
              type="button" 
              onClick={() => setShowSources(!showSources)}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
              {showSources ? 'Masquer la recherche de sources' : 'Rechercher des sources juridiques'}
            </button>
          </div>
          
          {showSources && (
            <div className="mt-3 p-3 border border-gray-200 rounded-md bg-gray-50">
              <div className="flex gap-2 mb-3">
                <select
                  value={selectedDocType}
                  onChange={(e) => setSelectedDocType(e.target.value)}
                  className="flex-grow px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="">Tous les types de documents</option>
                  {documentTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={searchSources}
                  disabled={isSearchingSources}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50"
                >
                  {isSearchingSources ? 'Recherche...' : 'Rechercher'}
                </button>
              </div>
              
              {sources.length > 0 ? (
                <div className="max-h-60 overflow-y-auto">
                  <h4 className="font-medium mb-2">Résultats ({sources.length})</h4>
                  <ul className="divide-y divide-gray-200">
                    {sources.map((source) => (
                      <li key={source.id} className="py-2">
                        <div className="flex justify-between">
                          <div>
                            <h5 className="font-medium">{source.title}</h5>
                            <p className="text-sm text-gray-600">
                              {source.type} • {source.date}
                            </p>
                            <p className="text-sm mt-1 line-clamp-2">
                              {source.content.substring(0, 150)}...
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => selectSource(source)}
                            className="self-start ml-2 px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                          >
                            Ajouter
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : isSearchingSources ? (
                <p className="text-center py-4 text-gray-500">Recherche en cours...</p>
              ) : (
                <p className="text-center py-4 text-gray-500">
                  Aucun résultat à afficher. Saisissez votre requête et cliquez sur Rechercher.
                </p>
              )}
            </div>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label htmlFor="context" className="block text-sm font-medium text-gray-700">
              Contexte supplémentaire
            </label>
            <span className="text-xs text-gray-500">(Optionnel)</span>
          </div>
          <textarea
            id="context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Ajoutez du contexte ou des détails spécifiques à votre situation..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            rows="4"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isSubmitting ? 'En cours de traitement...' : 'Obtenir une réponse juridique'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default QueryForm; 