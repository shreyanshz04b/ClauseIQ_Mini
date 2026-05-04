"""
Legal Sections Data Loader
Parses and normalizes legal sections from CSV and JSON files
"""

import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional
import re

class LegalSectionLoader:
    def __init__(self, data_dir: str = "app/data"):
        self.data_dir = Path(data_dir)
        self.sections = []
        self.index = {}  # section_id -> section data
        self.act_index = {}  # act_name -> list of sections
        
    def normalize_section(self, section_data: Dict, act_name: str, source: str) -> Dict:
        """Normalize section data to common format"""
        section_id = f"{act_name.upper()}-{section_data.get('section', '')}"
        
        # Extract description and ensure proper formatting
        description = section_data.get('description', '') or section_data.get('text', '')
        if isinstance(description, str):
            description = description.strip()
        else:
            description = str(description)
        
        # Extract title
        title = section_data.get('title', '') or section_data.get('name', '')
        if isinstance(title, str):
            title = title.strip()
        else:
            title = str(title)
        
        # Extract keywords from title and description
        keywords = self._extract_keywords(title, description)
        
        return {
            'id': section_id,
            'section_number': str(section_data.get('section', '')),
            'act_name': act_name,
            'title': title,
            'description': description[:500],  # First 500 chars for preview
            'full_description': description,
            'keywords': keywords,
            'source': source,
            'category': self._categorize_section(act_name)
        }
    
    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """Extract keywords from title and description"""
        keywords = []
        
        # Common legal keywords
        legal_terms = [
            'contract', 'agreement', 'liability', 'defendant', 'plaintiff',
            'evidence', 'punishment', 'offense', 'penalty', 'damages',
            'jurisdiction', 'appeal', 'procedure', 'witness', 'document',
            'property', 'inheritance', 'custody', 'bail', 'arrest',
            'crime', 'civil', 'criminal', 'right', 'duty', 'obligation'
        ]
        
        # Extract from title
        title_lower = title.lower()
        for term in legal_terms:
            if term in title_lower:
                keywords.append(term)
        
        # Extract from description (limit to first 200 chars)
        desc_lower = description[:200].lower()
        for term in legal_terms:
            if term in desc_lower and term not in keywords:
                keywords.append(term)
        
        return list(set(keywords[:5]))  # Return unique, max 5 keywords
    
    def _categorize_section(self, act_name: str) -> str:
        """Categorize section by act"""
        categories = {
            'IPC': 'Criminal Law',
            'CrPC': 'Criminal Procedure',
            'CPC': 'Civil Procedure',
            'BNS': 'Criminal Law',
            'HMA': 'Family Law',
            'IDA': 'Property/Debt',
            'IEA': 'Evidence',
            'NIA': 'National Security'
        }
        return categories.get(act_name, 'General Law')
    
    def load_json_file(self, filename: str, act_name: str):
        """Load and parse JSON file containing sections"""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            sections = data if isinstance(data, list) else data.get('sections', [])
            
            count = 0
            for section_data in sections:
                normalized = self.normalize_section(section_data, act_name, filename)
                self.sections.append(normalized)
                self.index[normalized['id']] = normalized
                
                # Index by act name
                if act_name not in self.act_index:
                    self.act_index[act_name] = []
                self.act_index[act_name].append(normalized)
                count += 1
            
            print(f"Loaded {count} sections from {filename}")
            return count
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            return 0
    
    def load_csv_file(self, filename: str, act_name: str):
        """Load and parse CSV file containing sections"""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            print(f"Warning: {filename} not found")
            return 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    # Convert CSV row to standard format
                    section_data = {
                        'section': row.get('Section', row.get('section', '')),
                        'title': row.get('Title', row.get('title', row.get('Name', ''))),
                        'description': row.get('Description', row.get('description', ''))
                    }
                    
                    if section_data['section'] and section_data['title']:
                        normalized = self.normalize_section(section_data, act_name, filename)
                        self.sections.append(normalized)
                        self.index[normalized['id']] = normalized
                        
                        if act_name not in self.act_index:
                            self.act_index[act_name] = []
                        self.act_index[act_name].append(normalized)
                        count += 1
                
                print(f"Loaded {count} sections from {filename}")
                return count
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            return 0
    
    def load_all_sections(self):
        """Load all legal sections from available files"""
        files_config = [
            ('bns_sections.csv', 'BNS'),
            ('cpc.json', 'CPC'),
            ('crpc.json', 'CrPC'),
            ('hma.json', 'HMA'),
            ('ida.json', 'IDA'),
            ('iea.json', 'IEA'),
            ('nia.json', 'NIA'),
        ]
        
        total_loaded = 0
        
        for filename, act_name in files_config:
            if filename.endswith('.json'):
                total_loaded += self.load_json_file(filename, act_name)
            elif filename.endswith('.csv'):
                total_loaded += self.load_csv_file(filename, act_name)
        
        print(f"Total sections loaded: {total_loaded}")
        return total_loaded
    
    def search_sections(self, query: str, act_filter: Optional[str] = None) -> List[Dict]:
        """Search sections using fuzzy matching and keyword search"""
        query_lower = query.lower()
        results = []
        
        for section in self.sections:
            # Apply act filter if provided
            if act_filter and section['act_name'] != act_filter:
                continue
            
            # Search in section number, title, keywords, and description
            match_score = 0
            
            # Exact matches score higher
            if query_lower in section['section_number'].lower():
                match_score += 10
            
            if query_lower in section['title'].lower():
                match_score += 8
            
            # Keyword matches
            for keyword in section['keywords']:
                if query_lower in keyword.lower():
                    match_score += 5
            
            # Description search
            if query_lower in section['full_description'].lower():
                match_score += 2
            
            if match_score > 0:
                results.append((section, match_score))
        
        # Sort by match score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return [result[0] for result in results]
    
    def get_section_by_id(self, section_id: str) -> Optional[Dict]:
        """Get section by ID"""
        return self.index.get(section_id)
    
    def get_sections_by_act(self, act_name: str) -> List[Dict]:
        """Get all sections for an act"""
        return self.act_index.get(act_name, [])
    
    def get_all_acts(self) -> List[str]:
        """Get list of all acts"""
        return sorted(list(self.act_index.keys()))
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded sections"""
        return {
            'total_sections': len(self.sections),
            'total_acts': len(self.act_index),
            'acts': {act: len(sections) for act, sections in self.act_index.items()}
        }


# Global instance
_loader = None

def get_loader():
    """Get or create the global loader instance"""
    global _loader
    if _loader is None:
        _loader = LegalSectionLoader()
        _loader.load_all_sections()
    return _loader

def reload_loader():
    """Reload the global loader instance"""
    global _loader
    _loader = LegalSectionLoader()
    _loader.load_all_sections()
    return _loader
