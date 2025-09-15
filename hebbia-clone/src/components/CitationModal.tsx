'use client';

import React from 'react';
import { Citation } from '../types/matrix';

interface CitationModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export default function CitationModal({ citation, onClose }: CitationModalProps) {
  if (!citation) return null;

  // Helper function to create Google Drive link
  const getGoogleDriveUrl = (documentName: string): string => {
    // Extract file ID from document name if it contains one, or create search URL
    const fileIdMatch = documentName.match(/(\d{4}-\d{4}-\d{4})/);
    if (fileIdMatch) {
      // If we have a file ID pattern, create a direct search
      return `https://drive.google.com/drive/search?q=${encodeURIComponent(documentName)}`;
    }
    // Otherwise, create a general search URL
    return `https://drive.google.com/drive/search?q=${encodeURIComponent(documentName.split(' ').slice(0, 3).join(' '))}`;
  };

  const handleDocumentClick = () => {
    const driveUrl = getGoogleDriveUrl(citation.documentName);
    window.open(driveUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Citation Details</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          {/* Extracted Value */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-2">
              {citation.columnName}
            </label>
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-md">
              <p className="text-gray-800 text-sm leading-relaxed">
                &ldquo;{citation.value}&rdquo;
              </p>
            </div>
          </div>

          {/* Source Information */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-2">
              Source Reference
            </label>
            <div className="bg-gray-50 border border-gray-200 p-4 rounded-md">
              <p className="text-gray-700 text-sm">
                {citation.source}
              </p>
              {citation.pageNumber && (
                <p className="text-gray-600 text-xs mt-2">
                  📄 {citation.pageNumber}
                </p>
              )}
            </div>
          </div>

          {/* Document Information */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-2">
              Source Document
            </label>
            <div className="flex items-center justify-between bg-gray-50 border border-gray-200 p-4 rounded-md">
              <div className="flex-1">
                <p className="text-gray-800 text-sm font-medium mb-1">
                  {citation.documentName}
                </p>
                <p className="text-gray-600 text-xs">
                  📁 Located in your Google Drive data room
                </p>
              </div>
              <button
                onClick={handleDocumentClick}
                className="ml-4 bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-md flex items-center gap-2 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open in Drive
              </button>
            </div>
          </div>

          {/* Additional Context */}
          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-md">
            <div className="flex">
              <svg className="w-5 h-5 text-yellow-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="text-yellow-800 text-sm font-medium">
                  How to find this in the document:
                </p>
                <p className="text-yellow-700 text-sm mt-1">
                  • Click &ldquo;Open in Drive&rdquo; to view the source document
                  • Use Ctrl+F (Cmd+F on Mac) to search for key terms from the extracted text
                  • Look for the page number reference if provided
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}