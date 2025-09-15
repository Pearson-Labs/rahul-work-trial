'use client';

import { useState } from 'react';
import { useBackendApi } from '../lib/api'; // Import the custom hook
import { GOOGLE_DRIVE_CONFIG } from '../config/drive';
import MatrixTable from '../components/MatrixTable';

type AnalysisType = 'general' | 'risk' | 'compliance';

export default function MatrixPage() {
  const [prompt, setPrompt] = useState('Scan all third-party contracts and virtual data room documents for any change-of-control provisions, termination-for-convenience clauses, or non-solicitation clauses that would be triggered by this acquisition. Present a summary of each risk identified, citing the source document and page number.');
  const [analysisType] = useState<AnalysisType>('general');
  const [generatedColumns, setGeneratedColumns] = useState<string[]>([]); // New state for dynamically generated columns
  const [data, setData] = useState<Record<string, Record<string, { value: string; source: string }>>>({});
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [specializedResult, setSpecializedResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false); // New state for ingestion loading
  const { callBackendApi } = useBackendApi(); // Use the custom hook

  const handleExtract = async () => {
    setIsLoading(true);
    setData({});
    setGeneratedColumns([]);
    setSpecializedResult(null);
    
    try {
      if (analysisType === 'general') {
        // Use the regular matrix extraction endpoint
        const result = await callBackendApi('/api/process', 'POST', { 
          prompt, 
          analysis_type: analysisType 
        });
        setGeneratedColumns(result.columns || []);
        setData(result.data || {});
      } else {
        // Use the specialized analysis endpoint
        const result = await callBackendApi('/api/analyze-specialized', 'POST', { 
          prompt, 
          analysis_type: analysisType 
        });
        setSpecializedResult(result);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      // You could add a state here to show an error message to the user
    } finally {
      setIsLoading(false);
    }
  };

  const handleIngest = async () => {
    setIsIngesting(true);
    try {
      // Check if Google Drive is configured
      if (!GOOGLE_DRIVE_CONFIG.FOLDER_ID) {
        alert("🔧 Setup Required!\n\nPlease configure your Google Drive folder ID in:\n/src/config/drive.ts\n\nSee GOOGLE_DRIVE_SETUP.md for detailed instructions.");
        return;
      }
      
      const result = await callBackendApi('/api/ingest-documents', 'POST', { 
        folder_id: GOOGLE_DRIVE_CONFIG.FOLDER_ID 
      });
      
      console.log("Ingestion successful:", result);
      alert(`✅ ${result.message}\n\nFiles processed: ${result.files_processed || 0}\nChunks ingested: ${result.chunks_ingested || 0}\nVector store: ${result.vector_store || 'pinecone'}`);
    } catch (error) {
      console.error("Error during ingestion:", error);
      alert(`❌ Error during ingestion: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/30">
      {/* Top Navigation Bar */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-40 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">Matrix</h1>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleIngest}
                disabled={isIngesting}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isIngesting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Ingesting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    Ingest Documents
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Query Input Section */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                What would you like to extract from your documents?
              </label>
              <div className="flex items-center bg-gray-50 border border-gray-200 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
                <div className="pl-4 pr-2">
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleExtract()}
                  placeholder="e.g., Extract payment terms, indemnification limits, and termination clauses..."
                  className="flex-1 px-2 py-4 bg-transparent border-none focus:outline-none focus:ring-0 text-gray-900 placeholder-gray-500"
                />
                <button
                  onClick={handleExtract}
                  disabled={isLoading}
                  className="px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {isLoading ? (
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  )}
                  <span className="font-medium">Extract</span>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Results Display */}
        {analysisType === 'general' ? (
          /* Enhanced Matrix Table for General Analysis */
          <MatrixTable
            columns={generatedColumns}
            data={data}
            isLoading={isLoading}
            query={prompt}
          />
        ) : (
          /* Specialized Analysis Results */
          <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
            {isLoading ? (
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                <div className="space-y-3">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  <div className="h-4 bg-gray-200 rounded w-4/6"></div>
                </div>
              </div>
            ) : specializedResult ? (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
                  {specializedResult.analysis_type} Analysis Results
                </h2>
                <div className="prose max-w-none">
                  {specializedResult.result?.analysis && (
                    <div className="whitespace-pre-wrap text-gray-700">
                      {specializedResult.result.analysis}
                    </div>
                  )}
                  {specializedResult.result?.compliance_report && (
                    <div className="whitespace-pre-wrap text-gray-700">
                      {specializedResult.result.compliance_report}
                    </div>
                  )}
                  {specializedResult.result?.columns && specializedResult.result?.data && (
                    <div className="mt-6">
                      <h3 className="text-md font-medium text-gray-800 mb-3">Structured Results:</h3>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Document</th>
                              {specializedResult.result.columns.map((col: string) => (
                                <th key={col} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{col}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {Object.entries(specializedResult.result.data).map(([docName, rowData]) => (
                              <tr key={docName}>
                                <td className="px-4 py-2 text-sm font-medium text-gray-800">{docName}</td>
                                {specializedResult.result.columns.map((col: string) => (
                                  <td key={col} className="px-4 py-2 text-sm text-gray-600">
                                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                    {(rowData as Record<string, any>)[col]?.value || 'N/A'}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                Run an analysis to see results here
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}