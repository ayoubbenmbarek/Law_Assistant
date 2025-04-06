import React, { useState } from 'react';
import { FaExternalLinkAlt, FaSearch, FaInfoCircle } from 'react-icons/fa';

/**
 * Composant pour afficher une liste de sources juridiques avec possibilité de filtrer
 * et de visualiser les détails d'une source.
 */
const SourceList = ({ sources, onSourceSelect, showTitle = true }) => {
  const [filter, setFilter] = useState('');
  
  // Filtrer les sources selon le terme de recherche
  const filteredSources = sources.filter(source => {
    if (!filter) return true;
    
    const searchTerm = filter.toLowerCase();
    return (
      source.title.toLowerCase().includes(searchTerm) || 
      source.type.toLowerCase().includes(searchTerm) ||
      (source.content && source.content.toLowerCase().includes(searchTerm))
    );
  });
  
  // Formater la date en format français
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
  
  // Tronquer le texte s'il est trop long
  const truncateText = (text, maxLength = 150) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      {showTitle && (
        <h2 className="text-xl font-semibold mb-4">Sources juridiques ({sources.length})</h2>
      )}
      
      {sources.length > 3 && (
        <div className="mb-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FaSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filtrer les sources..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
        </div>
      )}
      
      {filteredSources.length === 0 ? (
        <div className="text-center py-4 text-gray-500">
          {filter ? 'Aucune source ne correspond à votre recherche' : 'Aucune source disponible'}
        </div>
      ) : (
        <ul className="divide-y divide-gray-200 max-h-[500px] overflow-y-auto">
          {filteredSources.map((source) => (
            <li key={source.id} className="py-3">
              <div className="flex justify-between">
                <div className="flex-1 min-w-0 pr-4">
                  <h4 className="text-sm font-medium text-gray-900 truncate">{source.title}</h4>
                  <div className="flex flex-wrap gap-1 mt-1 mb-1">
                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-800 text-xs font-medium rounded">
                      {source.type}
                    </span>
                    {source.date && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs font-medium rounded">
                        {formatDate(source.date)}
                      </span>
                    )}
                    {source.score && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">
                        Score: {Math.round(source.score * 100)}%
                      </span>
                    )}
                  </div>
                  {source.content && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                      {truncateText(source.content)}
                    </p>
                  )}
                </div>
                <div className="flex items-start space-x-2">
                  <button
                    onClick={() => onSourceSelect(source.id)}
                    className="p-1 text-indigo-600 hover:text-indigo-900 rounded-full hover:bg-gray-100"
                    title="Voir les détails"
                  >
                    <FaInfoCircle />
                  </button>
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1 text-gray-500 hover:text-gray-900 rounded-full hover:bg-gray-100"
                      title="Voir la source originale"
                    >
                      <FaExternalLinkAlt />
                    </a>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SourceList; 