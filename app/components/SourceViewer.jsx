import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaExternalLinkAlt, FaFilePdf, FaCopy, FaArrowLeft } from 'react-icons/fa';

/**
 * Composant pour afficher les détails d'une source juridique
 */
const SourceViewer = ({ sourceId, onClose }) => {
  const [source, setSource] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSource = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await axios.get(`/api/sources/${sourceId}`);
        setSource(response.data);
      } catch (error) {
        console.error('Erreur lors du chargement de la source:', error);
        setError(error.response?.data?.detail || 'Impossible de charger les détails de cette source');
      } finally {
        setLoading(false);
      }
    };

    if (sourceId) {
      fetchSource();
    }
  }, [sourceId]);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        alert('Copié dans le presse-papier');
      })
      .catch(err => {
        console.error('Erreur lors de la copie:', err);
        alert('Échec de la copie');
      });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      }).format(date);
    } catch (error) {
      return dateString;
    }
  };

  const formatCitation = () => {
    if (!source) return '';
    
    return `${source.title}, ${source.type}, ${formatDate(source.date)}${source.url ? `, disponible sur: ${source.url}` : ''}`;
  };

  if (loading) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Chargement de la source...</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <FaArrowLeft />
          </button>
        </div>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
          <div className="h-20 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Erreur</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <FaArrowLeft />
          </button>
        </div>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!source) {
    return null;
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Détails de la source</h2>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          <FaArrowLeft />
        </button>
      </div>

      <div className="mb-4">
        <h3 className="text-lg font-medium mb-2">{source.title}</h3>
        <div className="flex flex-wrap gap-2 mb-2">
          <span className="px-2 py-1 bg-indigo-100 text-indigo-800 text-xs font-medium rounded">
            {source.type}
          </span>
          {source.metadata?.source && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
              {source.metadata.source}
            </span>
          )}
          {source.date && (
            <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-medium rounded">
              {formatDate(source.date)}
            </span>
          )}
        </div>
      </div>

      <div className="mb-6">
        <div className="bg-gray-50 p-4 rounded border border-gray-200 mb-2">
          <div className="max-h-96 overflow-y-auto whitespace-pre-wrap">
            {source.content}
          </div>
        </div>
        <div className="flex justify-end">
          <button
            onClick={() => copyToClipboard(source.content)}
            className="flex items-center text-xs text-gray-600 hover:text-gray-900"
          >
            <FaCopy className="mr-1" /> Copier le texte
          </button>
        </div>
      </div>

      {source.metadata && Object.keys(source.metadata).length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-2">Métadonnées</h4>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            {Object.entries(source.metadata).map(([key, value]) => (
              <React.Fragment key={key}>
                <dt className="font-medium text-gray-500">{key}</dt>
                <dd className="text-gray-700">
                  {typeof value === 'object' ? JSON.stringify(value) : value.toString()}
                </dd>
              </React.Fragment>
            ))}
          </dl>
        </div>
      )}

      <div className="border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium mb-2">Citation</h4>
        <div className="bg-gray-50 p-3 rounded border border-gray-200 text-sm text-gray-700 mb-2">
          {formatCitation()}
        </div>
        <div className="flex justify-between">
          <button
            onClick={() => copyToClipboard(formatCitation())}
            className="flex items-center text-xs text-gray-600 hover:text-gray-900"
          >
            <FaCopy className="mr-1" /> Copier la citation
          </button>
          
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-xs text-indigo-600 hover:text-indigo-900"
            >
              <FaExternalLinkAlt className="mr-1" /> Voir la source originale
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default SourceViewer; 