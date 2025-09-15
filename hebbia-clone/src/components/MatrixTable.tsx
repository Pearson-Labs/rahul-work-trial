'use client';

import React from 'react';
import { MatrixData } from '../types/matrix';
import MatrixCell from './MatrixCell';


interface MatrixTableProps {
  columns: string[];
  data: MatrixData;
  isLoading: boolean;
  query: string;
}

export default function MatrixTable({ columns, data, isLoading, query }: MatrixTableProps) {
  

  // Statistics
  const documentCount = Object.keys(data).length;
  const totalExtractions = Object.values(data).reduce((total, docData) => {
    return total + Object.values(docData).filter(cell =>
      cell && cell.value && cell.value !== 'N/A' && cell.value !== 'Not found'
    ).length;
  }, 0);

  return (
    <>
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
        {/* Header with query and stats */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Analysis Results
              </h2>
              <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                &ldquo;{query}&rdquo;
              </p>
              <div className="flex items-center gap-6 text-sm">
                <span className="flex items-center gap-2 text-blue-700">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {documentCount} Documents
                </span>
                <span className="flex items-center gap-2 text-green-700">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  {totalExtractions} Extractions
                </span>
                <span className="flex items-center gap-2 text-purple-700">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                  {columns.length} Columns
                </span>
              </div>
            </div>

            {/* Help text */}
            <div className="hidden lg:block">
              <div className="bg-white/70 backdrop-blur-sm border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
                <div className="flex items-center gap-2 mb-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="font-medium">How to use:</span>
                </div>
                <ul className="space-y-1">
                  <li>• Click any cell to view citation details</li>
                  <li>• Click &ldquo;Open in Drive&rdquo; to view source documents</li>
                  <li>• Hover cells to preview source information</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="sticky left-0 bg-gray-50 px-6 py-4 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider border-r border-gray-200 shadow-sm z-10">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Document
                  </div>
                </th>
                {columns.map((col, index) => (
                  <th key={col} className="px-6 py-4 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        index === 0 ? 'bg-blue-400' :
                        index === 1 ? 'bg-green-400' :
                        index === 2 ? 'bg-purple-400' :
                        index === 3 ? 'bg-orange-400' :
                        'bg-pink-400'
                      }`}></div>
                      {col}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="sticky left-0 bg-white px-6 py-4 border-r border-gray-100 shadow-sm">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gray-200 rounded-lg flex-shrink-0"></div>
                        <div className="h-4 bg-gray-200 rounded w-48"></div>
                      </div>
                    </td>
                    {columns.map(col => (
                      <td key={col} className="px-6 py-4">
                        <div className="space-y-2">
                          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                          <div className="h-3 bg-gray-100 rounded w-1/2"></div>
                        </div>
                      </td>
                    ))}
                  </tr>
                ))
              ) : documentCount === 0 ? (
                // Empty state
                <tr>
                  <td colSpan={columns.length + 1} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-4 text-gray-500">
                      <svg className="w-16 h-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div>
                        <p className="text-lg font-medium text-gray-900 mb-1">No results yet</p>
                        <p className="text-gray-600">Enter a query above to analyze your documents</p>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                // Data rows
                Object.entries(data).map(([ docName, rowData ]) => (
                  <tr key={docName} className="hover:bg-gray-50/50 transition-colors">
                    {/* Document name - sticky column */}
                    <td className="sticky left-0 bg-white px-6 py-4 border-r border-gray-100 shadow-sm group-hover:bg-gray-50/50">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-center justify-center flex-shrink-0">
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {docName.length > 50 ? docName.substring(0, 47) + '...' : docName}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            Legal Document
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Data cells */}
                    {columns.map(col => (
                      <MatrixCell
                        key={col}
                        data={rowData[col] || null}
                        documentName={docName}
                        columnName={col}
                      />
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer with export options */}
        {!isLoading && documentCount > 0 && (
          <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                Showing {documentCount} documents with {totalExtractions} total extractions
              </span>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-3 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export CSV
                </button>
                <button className="flex items-center gap-2 px-3 py-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                  </svg>
                  Share
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      
    </>
  );
}