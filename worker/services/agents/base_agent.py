"""
Base class for specialist AI agents.
Each agent handles both triage (which listings are interesting?) and deep analysis (should we notify?).
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for specialist agents.
    Each agent handles BOTH triage and deep analysis for its category.
    
    Two-pass flow:
    1. triage_batch() - Quick scan of many listings to find interesting ones
    2. analyze() - Deep multimodal analysis of a single interesting listing
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the agent with Gemini API client.
        
        Args:
            api_key: Google AI API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.client = None
        
        if not self.api_key:
            logger.warning(
                f"{self.agent_type}: GEMINI_API_KEY or GOOGLE_API_KEY not found. "
                f"Agent will not function without API key."
            )
            return
        
        # Initialize the Gemini client
        self.client = genai.Client(api_key=self.api_key)
        logger.info(f"{self.agent_type} agent initialized")
    
    @property
    @abstractmethod
    def agent_type(self) -> str:
        """
        Agent type identifier (e.g., 'skis', 'vehicles', 'dj_equipment').
        Used for tracking and routing.
        """
        pass
    
    @property
    @abstractmethod
    def triage_prompt(self) -> str:
        """
        System prompt for the triage pass.
        Should describe what makes a listing interesting for this category.
        """
        pass
    
    @property
    @abstractmethod
    def analysis_prompt(self) -> str:
        """
        System prompt for the deep analysis pass.
        Should include detailed evaluation criteria and output format.
        """
        pass
    
    @property
    def enabled(self) -> bool:
        """
        Whether this agent is enabled and ready to process listings.
        Override to False for stub agents.
        """
        return True
    
    @property
    def triage_model(self) -> str:
        """Model to use for triage (default: Gemini 2.5 Pro for quality)."""
        return 'gemini-2.5-pro'
    
    @property
    def analysis_model(self) -> str:
        """Model to use for deep analysis (default: Gemini 2.5 Pro for quality)."""
        return 'gemini-2.5-pro'
    
    # Maximum listings per LLM call to avoid token limit truncation
    TRIAGE_BATCH_SIZE = 20
    
    def triage_batch(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        PASS 1: Quick scan of a batch of listings to identify interesting ones.
        
        For large batches, this splits into chunks to avoid LLM output truncation.
        
        Args:
            listings: List of listing dictionaries with basic metadata:
                - idx: int (index in the batch)
                - title: str
                - price: str
                - location: str
                - thumbnail_url: str (optional)
        
        Returns:
            List of triage results:
                - listing_idx: int
                - interesting: bool
                - confidence: int (0-100)
                - reason: str
        """
        if not self.enabled:
            raise NotImplementedError(f"{self.agent_type} agent is not enabled")
        
        if not self.client:
            raise ValueError(f"{self.agent_type} agent: API key not configured")
        
        # Split large batches into smaller chunks to avoid output truncation
        if len(listings) > self.TRIAGE_BATCH_SIZE:
            logger.info(
                f"{self.agent_type}: Splitting {len(listings)} listings into chunks of {self.TRIAGE_BATCH_SIZE}"
            )
            all_results = []
            total_tokens = 0
            
            for i in range(0, len(listings), self.TRIAGE_BATCH_SIZE):
                chunk = listings[i:i + self.TRIAGE_BATCH_SIZE]
                chunk_num = (i // self.TRIAGE_BATCH_SIZE) + 1
                total_chunks = (len(listings) + self.TRIAGE_BATCH_SIZE - 1) // self.TRIAGE_BATCH_SIZE
                logger.info(f"{self.agent_type}: Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} listings)")
                
                chunk_results = self._triage_single_batch(chunk)
                all_results.extend(chunk_results)
            
            # Log combined results
            interesting_count = sum(1 for r in all_results if r['interesting'])
            logger.info(
                f"{self.agent_type} triage complete: {interesting_count}/{len(listings)} listings interesting"
            )
            
            return all_results
        else:
            return self._triage_single_batch(listings)
    
    def _triage_single_batch(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Triage a single batch of listings (internal method).
        
        This is the actual LLM call - should be called with <= TRIAGE_BATCH_SIZE listings.
        """
        try:
            # Build the triage prompt with all listings
            listings_text = self._format_listings_for_triage(listings)
            prompt = f"{self.triage_prompt}\n\n{listings_text}"
            
            # Call LLM for batch triage
            response_text, token_usage = self._call_llm(
                prompt=prompt,
                model=self.triage_model,
                system_instruction=self.triage_prompt
            )
            
            # Parse results
            results = self._parse_triage_response(response_text, len(listings))
            
            # Log results
            interesting_count = sum(1 for r in results if r['interesting'])
            logger.info(
                f"{self.agent_type} triage: {interesting_count}/{len(listings)} listings interesting "
                f"(tokens: {token_usage['total_tokens']})"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"{self.agent_type} triage error: {e}")
            # Return all as not interesting on error
            return [
                {
                    'listing_idx': listing['idx'],
                    'interesting': False,
                    'confidence': 0,
                    'reason': f'Error during triage: {str(e)}'
                }
                for listing in listings
            ]
    
    @abstractmethod
    def analyze(self, listing_data: Dict[str, Any], images: Optional[List[bytes]] = None) -> Dict[str, Any]:
        """
        PASS 2: Deep analysis of a single interesting listing.
        
        Args:
            listing_data: Full listing information including:
                - title: str
                - price: str
                - location: str
                - url: str
                - description: str (full description)
            images: Optional list of image bytes for multimodal analysis
        
        Returns:
            Analysis result dictionary:
                - recommendation: str ('NOTIFY' or 'IGNORE')
                - confidence: int (0-100)
                - summary: str
                - detailed analysis fields (agent-specific)
                - token_usage: dict (if available)
        """
        pass
    
    def _call_llm(
        self, 
        prompt: str, 
        images: Optional[List[bytes]] = None,
        model: Optional[str] = None,
        system_instruction: Optional[str] = None,
        response_format: str = 'json'
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Call Gemini API and return response text and token usage.
        
        Args:
            prompt: The prompt text
            images: Optional list of image bytes
            model: Model name to use (defaults to analysis_model)
            system_instruction: System instruction for the model
            response_format: 'json' or 'text'
        
        Returns:
            Tuple of (response_text, token_usage_dict)
        """
        if not self.client:
            raise ValueError("API client not initialized")
        
        model = model or self.analysis_model
        
        # Prepare content
        content = [prompt]
        if images:
            for img_bytes in images:
                if img_bytes:
                    content.append(types.Part(inline_data=types.Blob(
                        mime_type='image/jpeg',
                        data=img_bytes
                    )))
        
        # Configure generation
        # Using 16384 tokens to handle large batch responses without truncation
        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.8,
            max_output_tokens=16384,
            response_mime_type='application/json' if response_format == 'json' else 'text/plain'
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
        
        # Generate
        response = self.client.models.generate_content(
            model=model,
            contents=content,
            config=config
        )
        
        # Extract token usage
        token_usage = {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0,
            'model': model
        }
        
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            token_usage = {
                'prompt_tokens': usage.prompt_token_count,
                'completion_tokens': usage.candidates_token_count,
                'total_tokens': usage.total_token_count,
                'model': model
            }
        
        return response.text, token_usage
    
    def _format_listings_for_triage(self, listings: List[Dict[str, Any]]) -> str:
        """Format listings for the triage prompt."""
        lines = ["LISTINGS TO REVIEW:"]
        for listing in listings:
            lines.append(
                f"{listing['idx']}. Title: \"{listing.get('title', 'Unknown')}\" | "
                f"Price: {listing.get('price', 'Unknown')} | "
                f"Location: {listing.get('location', 'Unknown')}"
            )
        
        lines.append("\nRespond with a JSON array of objects, one for each listing:")
        lines.append('[{"listing_idx": 0, "interesting": true, "confidence": 85, "reason": "..."},]')
        
        return '\n'.join(lines)
    
    def _parse_triage_response(self, response_text: str, num_listings: int) -> List[Dict[str, Any]]:
        """
        Parse triage response JSON into structured results.
        
        Args:
            response_text: Raw JSON response from LLM
            num_listings: Expected number of listings
        
        Returns:
            List of triage results
        """
        try:
            # Clean up response
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```'):
                lines = text.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                text = '\n'.join(lines)
            
            # Parse JSON
            results = json.loads(text)
            
            # Validate
            if not isinstance(results, list):
                raise ValueError("Expected JSON array")
            
            # Ensure we have results for all listings
            if len(results) != num_listings:
                logger.warning(
                    f"Triage returned {len(results)} results for {num_listings} listings. "
                    f"Filling missing entries."
                )
                # Create default entries for missing listings
                existing_indices = {r.get('listing_idx') for r in results if 'listing_idx' in r}
                for i in range(num_listings):
                    if i not in existing_indices:
                        results.append({
                            'listing_idx': i,
                            'interesting': False,
                            'confidence': 0,
                            'reason': 'No triage result returned'
                        })
            
            return results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse triage response as JSON: {e}")
            logger.error(f"Response: {response_text[:500]}")
            # Return all as not interesting
            return [
                {
                    'listing_idx': i,
                    'interesting': False,
                    'confidence': 0,
                    'reason': 'Failed to parse triage response'
                }
                for i in range(num_listings)
            ]
    
    def _calculate_cost(self, token_usage: Dict[str, Any]) -> Decimal:
        """
        Calculate estimated cost in USD based on token usage.
        
        Args:
            token_usage: Dictionary with prompt_tokens, completion_tokens, model
        
        Returns:
            Estimated cost as Decimal
        """
        model = token_usage.get('model', '')
        prompt_tokens = token_usage.get('prompt_tokens', 0)
        completion_tokens = token_usage.get('completion_tokens', 0)
        
        # Gemini pricing
        if 'flash' in model.lower() or '2.0' in model:
            # Gemini 2.0 Flash: Input $0.075/1M, Output $0.30/1M
            input_cost_per_million = Decimal('0.075')
            output_cost_per_million = Decimal('0.30')
        else:
            # Gemini 2.5 Pro: Input $1.25/1M, Output $10/1M
            input_cost_per_million = Decimal('1.25')
            output_cost_per_million = Decimal('10.0')
        
        input_cost = (Decimal(prompt_tokens) / Decimal('1000000')) * input_cost_per_million
        output_cost = (Decimal(completion_tokens) / Decimal('1000000')) * output_cost_per_million
        
        return input_cost + output_cost
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
