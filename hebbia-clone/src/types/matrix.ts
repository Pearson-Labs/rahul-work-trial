export interface CellData {
  value: string;
  source: string;
  source_text?: string;
  confidence?: number;
  page_numbers?: string[];
  page_number?: string; // Legacy support
  document_id?: string;
  document_url?: string;
  exact_quote?: string;
  location_markers?: string[];
}

export interface MatrixData {
  [documentName: string]: {
    [columnName: string]: CellData;
  };
}

export interface Citation {
  value: string;
  source: string;
  documentName: string;
  columnName: string;
  pageNumber?: string;
  documentUrl?: string;
}