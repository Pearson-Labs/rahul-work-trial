'use client';

import React, { useState } from 'react';
import { CellData } from '../types/matrix';

interface MatrixCellProps {
  data: CellData | null;
  documentName: string;
  columnName: string;
}

export default function MatrixCell({ data }: MatrixCellProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!data || !data.value || data.value === 'N/A' || data.value === 'Not found' || data.value === 'Not specified' || data.value === 'Not Found') {
    return (
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400 italic">
        —
      </td>
    );
  }

  const truncatedValue = data.value.length > 150 ? data.value.substring(0, 147) + '...' : data.value;
  const truncatedSource = data.source.length > 100 ? data.source.substring(0, 97) + '...' : data.source;

  // Enhanced data from the new structure
  const hasEnhancedData = data.page_numbers !== undefined || data.document_url !== undefined;
  const pageNumbers = data.page_numbers || [];
  const exactQuote = data.exact_quote || '';

  return (
    <td
      className="px-4 py-3 text-sm text-gray-700 relative group align-top"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div className="flex flex-col gap-1">
        {/* Main extracted value with clickable link */}
        <a
          href={data.document_url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className={`font-medium hover:underline transition-colors break-words ${
            data.document_url ? 'text-blue-600 hover:text-blue-800 cursor-pointer' : 'text-gray-700 cursor-default'
          }`}
          title={data.document_url ? 'Click to view in document' : 'No direct link available'}
        >
          {truncatedValue}
          {data.document_url && (
            <svg className="w-3 h-3 inline-block ml-1 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          )}
        </a>

        {/* Source information */}
        <div className="text-xs text-gray-500 italic break-words">
          <div className="flex items-center gap-2">
            <span>Source: {truncatedSource}</span>
            {pageNumbers.length > 0 && (
              <span className="bg-gray-100 px-1 rounded text-xs">
                Page {pageNumbers.join(', ')}
              </span>
            )}
          </div>
        </div>


        {/* Enhanced tooltip on hover */}
        {showTooltip && hasEnhancedData && (
          <div className="absolute z-50 left-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-3 w-80 text-xs">
            <div className="space-y-2">
              {exactQuote && (
                <div>
                  <span className="font-medium text-gray-700">Exact Quote:</span>
                  <p className="text-gray-600 mt-1 italic">&ldquo;{exactQuote.substring(0, 200)}&hellip;&rdquo;</p>
                </div>
              )}

              {pageNumbers.length > 0 && (
                <div>
                  <span className="font-medium text-gray-700">Page References:</span>
                  <p className="text-gray-600 mt-1">{pageNumbers.join(', ')}</p>
                </div>
              )}

              {data.document_url && (
                <div>
                  <span className="font-medium text-gray-700">Direct Link:</span>
                  <p className="text-blue-600 mt-1 break-all">Click value above to jump to exact location in document</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </td>
  );
}
