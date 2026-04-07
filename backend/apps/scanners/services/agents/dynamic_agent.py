"""
Dynamic Agent - Database-driven specialist agent.

This agent loads its prompts and configuration from the Agent database model,
replacing the need for hardcoded agent classes (SkiAgent, VehicleAgent, etc.).

The BaseAgent class already handles all common logic (LLM calls, triage batching,
response parsing, cost calculation). This class simply wires the database fields
into the abstract properties that BaseAgent requires.
"""
import json
import logging
from typing import Dict, Any, Optional, List

from google.genai import types

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DynamicAgent(BaseAgent):
    """
    Agent whose prompts and configuration come from the database.
    
    This is the single agent class used for ALL agent types. It replaces
    SkiAgent, VehicleAgent, DJEquipmentAgent, etc. with a unified
    implementation that reads its behavior from the Agent model.
    """
    
    def __init__(self, agent_record, **kwargs):
        """
        Initialize from a database Agent record.
        
        Args:
            agent_record: An instance of scanners.models.Agent
        """
        self._agent_record = agent_record
        super().__init__(**kwargs)
    
    @property
    def agent_type(self) -> str:
        return self._agent_record.slug
    
    @property
    def triage_prompt(self) -> str:
        return self._agent_record.triage_prompt
    
    @property
    def analysis_prompt(self) -> str:
        return self._agent_record.analysis_prompt
    
    @property
    def enabled(self) -> bool:
        return self._agent_record.enabled
    
    @property
    def triage_model(self) -> str:
        return self._agent_record.triage_model or 'gemini-2.5-pro'
    
    @property
    def analysis_model(self) -> str:
        return self._agent_record.analysis_model or 'gemini-2.5-pro'
    
    def analyze(self, listing_data: Dict[str, Any], images: Optional[List[bytes]] = None) -> Dict[str, Any]:
        """
        Deep analysis of a single listing using the agent's analysis prompt.
        
        This is a generalized version of the analyze() method that was previously
        duplicated across SkiAgent, VehicleAgent, and DJEquipmentAgent. The pattern
        is identical: build prompt -> call LLM -> parse JSON -> add metadata.
        """
        if not self.client:
            logger.error(f"{self.agent_type}: API key not configured")
            return self._create_error_response(
                "API key not configured. Please set GEMINI_API_KEY or GOOGLE_API_KEY in backend/.env"
            )
        
        try:
            # Build the analysis prompt with listing data
            prompt = self._build_analysis_user_prompt(listing_data)
            
            # Generate response using base class helper
            logger.info(f"Analyzing listing ({self.agent_type}): {listing_data.get('title', 'Unknown')}")
            response_text, token_usage = self._call_llm(
                prompt=prompt,
                images=images if images else None,
                model=self.analysis_model,
                system_instruction=self.analysis_prompt,
                response_format='json'
            )
            
            # Parse the response
            result = self._parse_analysis_response(response_text)
            
            # Add metadata
            result['analyzed_at'] = self._get_timestamp()
            result['model_used'] = self.analysis_model
            result['agent_type'] = self.agent_type
            result['is_mock'] = False
            result['images_analyzed'] = len(images) if images else 0
            result['token_usage'] = token_usage
            
            logger.info(
                f"{self.agent_type} analysis complete: {result.get('recommendation')} "
                f"(confidence: {result.get('confidence')}%) "
                f"[{result.get('images_analyzed', 0)} images, {token_usage['total_tokens']} tokens]"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during {self.agent_type} analysis: {e}")
            return self._create_error_response(str(e))
    
    def _build_analysis_user_prompt(self, listing_data: Dict[str, Any]) -> str:
        """
        Build the user prompt for deep analysis.
        
        This contains the listing data to analyze. The system instruction
        (self.analysis_prompt) provides the domain expertise and evaluation criteria.
        """
        return f"""
LISTING TO ANALYZE:
{'=' * 75}
Title: {listing_data.get('title', 'Unknown')}
Price: {listing_data.get('price', 'Unknown')}
Location: {listing_data.get('location', 'Unknown')}
URL: {listing_data.get('url', 'Unknown')}

SELLER'S DESCRIPTION:
{listing_data.get('description', 'No description provided')}

[IMAGES ATTACHED - Analyze for condition, model verification, and value assessment]

YOUR MISSION:
{'=' * 75}
1. IDENTIFY the exact item from photos and description
2. ASSESS condition from photos
3. CALCULATE market value and profit potential
4. DETERMINE: NOTIFY (buy it!) or IGNORE
5. Respond with valid JSON matching the format specified in your instructions.
"""
    
    def _parse_analysis_response(self, text: str) -> Dict[str, Any]:
        """
        Parse LLM analysis response into structured format.
        
        Handles markdown code block cleanup and JSON parsing.
        This is the same pattern used by all previous agent classes.
        """
        try:
            # Clean up response - remove markdown code blocks if present
            text = text.strip()
            
            if text.startswith('```'):
                lines = text.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                text = '\n'.join(lines)
            
            # Parse JSON
            result = json.loads(text)
            
            # Validate required fields (core schema)
            required_fields = ['recommendation', 'confidence', 'summary']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {self.agent_type} analysis response as JSON: {e}")
            logger.error(f"Response length: {len(text)} characters")
            logger.error(f"Response start: {text[:500]}")
            
            if not text.strip().endswith('}'):
                logger.error("Response appears truncated (doesn't end with '}')")
                raise ValueError(f"LLM response was truncated mid-JSON. Error: {e}")
            
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Error parsing {self.agent_type} analysis response: {e}")
            raise
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standard error response."""
        return {
            'recommendation': 'IGNORE',
            'confidence': 0,
            'summary': 'Analysis failed - please try again',
            'item_identification': {
                'description': 'Analysis error occurred',
                'brand': None,
                'model': None,
                'condition': 'Unknown'
            },
            'value_assessment': {
                'estimated_value': None,
                'savings_percent': 0,
                'explanation': f'Error: {error_message}'
            },
            'key_takeaways': {
                'positives': [],
                'negatives': [error_message]
            },
            'image_analysis': f'Error: {error_message}',
            'error': error_message,
            'is_mock': False
        }
