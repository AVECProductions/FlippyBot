export interface Scanner {
  id: number;
  category: string;
  query: string;
  town: string;
  location_id: number | null;
  status: string;
  locations_data?: ScannerLocationMapping[];
}

export interface ScannerLocationMapping {
  id: number;
  location: number;
  location_name: string;
  location_slug: string;
  is_active: boolean;
}

export interface Keyword {
  id: number;
  keyword: string;
  filterID: number;
} 