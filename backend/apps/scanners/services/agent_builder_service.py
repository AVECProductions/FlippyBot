"""
Agent Builder Service - AI-powered prompt generation for new agents.

Uses Gemini to generate triage and analysis prompts from natural language
descriptions of what the user wants the agent to look for.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# Meta-prompt that instructs the AI to generate agent prompts
AGENT_BUILDER_META_PROMPT = """You are an expert AI prompt engineer for FLIPPY, a marketplace deal-scanning platform.

Your job is to create TWO specialized prompts for a new AI agent that will scan Facebook Marketplace listings:

1. **TRIAGE PROMPT**: A system prompt for quickly scanning many listings (title + price + location only) 
   to decide which are "interesting" and worth deeper investigation.
   
2. **ANALYSIS PROMPT**: A system prompt for deep analysis of a single listing (with full description and images)
   to make a final NOTIFY or IGNORE recommendation.

═══════════════════════════════════════════════════════════════════════════════
HOW THE SYSTEM WORKS
═══════════════════════════════════════════════════════════════════════════════

Pass 1 (Triage): The agent reviews batches of listings with ONLY title, price, and location.
- Must output JSON: [{"listing_idx": 0, "interesting": true, "confidence": 85, "reason": "..."}]
- Goal: High recall - better to investigate a "maybe" than miss a deal.

Pass 2 (Deep Analysis): The agent gets full listing details + images for each interesting listing.
- Must output JSON with these REQUIRED fields:
  {
    "recommendation": "NOTIFY" or "IGNORE",
    "confidence": 0-100,
    "summary": "One-line deal summary",
    "item_identification": { "brand": "", "model": "", "condition": "", "size": "" },
    "value_assessment": { "asking_price": "", "estimated_value": "", "savings_percent": 0 },
    "key_takeaways": { "positives": [], "negatives": [] },
    "image_analysis": "What you observed in the images"
  }
- The agent may add domain-specific fields beyond these core fields.

═══════════════════════════════════════════════════════════════════════════════
PROMPT DESIGN PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════

1. PROFIT-FIRST: The user wants to find undervalued items for resale. Always include profit analysis.
2. DOMAIN EXPERTISE: Include specific brands, models, price ranges, and evaluation criteria for the category.
3. TIER SYSTEM: Organize items into tiers by value/desirability.
4. CLEAR DECISION LOGIC: Define exactly when to NOTIFY vs IGNORE.
5. VISUAL INTELLIGENCE: Tell the analysis prompt what to look for in images.
6. MARKET AWARENESS: Include typical used market values and what affects pricing.

═══════════════════════════════════════════════════════════════════════════════
YOUR OUTPUT FORMAT
═══════════════════════════════════════════════════════════════════════════════

Respond with EXACTLY this JSON (no markdown, no code blocks):
{
    "suggested_name": "Category Specialist",
    "suggested_slug": "category-slug",
    "suggested_icon": "emoji",
    "suggested_description": "One-line description of what this agent does",
    "triage_prompt": "The full triage system prompt...",
    "analysis_prompt": "The full analysis system prompt..."
}

Make the prompts thorough, detailed, and actionable. Include specific brand names,
model numbers, price ranges, and evaluation criteria. The better the prompts,
the better deals the agent will find."""


AGENT_REFINE_META_PROMPT = """You are an expert AI prompt engineer for FLIPPY, a marketplace deal-scanning platform.

The user has an existing agent with triage and analysis prompts. They want to refine or improve these prompts based on their feedback.

Your job is to take the CURRENT prompts and the user's FEEDBACK, then return IMPROVED versions of both prompts.

RULES:
- Preserve the core structure and JSON output format requirements
- Apply the user's feedback thoughtfully
- If the feedback is about triage, focus changes on the triage prompt (but update analysis if relevant)
- If the feedback is about analysis, focus changes on the analysis prompt
- Keep the profit-first marketplace deal-finding focus
- Maintain the tier system and decision logic structure

Respond with EXACTLY this JSON (no markdown, no code blocks):
{
    "triage_prompt": "The improved triage system prompt...",
    "analysis_prompt": "The improved analysis system prompt...",
    "changes_summary": "Brief description of what was changed and why"
}"""


class AgentBuilderService:
    """
    Service for AI-powered agent prompt generation and refinement.
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.client = None
        
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            logger.warning("AgentBuilderService: No API key found. Prompt generation will not work.")
    
    def generate_prompts(self, description: str) -> Dict[str, Any]:
        """
        Generate triage and analysis prompts from a natural language description.
        
        Args:
            description: What the user wants the agent to look for.
                e.g. "I want to find undervalued vintage guitars, especially Fender and Gibson"
        
        Returns:
            Dictionary with suggested_name, suggested_icon, triage_prompt, analysis_prompt
        """
        if not self.client:
            raise ValueError("API key not configured. Cannot generate prompts.")
        
        user_prompt = f"""Create a new marketplace deal-scanning agent based on this description:

USER'S REQUEST:
{description}

Generate thorough, detailed triage and analysis prompts that will help this agent find
profitable deals in this category. Include specific brands, models, price ranges,
and evaluation criteria relevant to this domain."""
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.4,
                top_p=0.9,
                max_output_tokens=16384,
                response_mime_type='application/json',
                system_instruction=AGENT_BUILDER_META_PROMPT
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[user_prompt],
                config=config
            )
            
            # Parse response
            result = json.loads(response.text)
            
            # Add token usage info
            token_usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                token_usage = {
                    'prompt_tokens': usage.prompt_token_count,
                    'completion_tokens': usage.candidates_token_count,
                    'total_tokens': usage.total_token_count,
                }
            
            result['token_usage'] = token_usage
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prompt generation response: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating prompts: {e}")
            raise
    
    def refine_prompts(
        self, 
        current_triage_prompt: str, 
        current_analysis_prompt: str, 
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine existing prompts based on user feedback.
        
        Args:
            current_triage_prompt: The current triage prompt
            current_analysis_prompt: The current analysis prompt
            feedback: What the user wants changed
        
        Returns:
            Dictionary with improved triage_prompt, analysis_prompt, changes_summary
        """
        if not self.client:
            raise ValueError("API key not configured. Cannot refine prompts.")
        
        user_prompt = f"""Here are the CURRENT prompts for this agent:

═══ CURRENT TRIAGE PROMPT ═══
{current_triage_prompt}

═══ CURRENT ANALYSIS PROMPT ═══
{current_analysis_prompt}

═══ USER'S FEEDBACK ═══
{feedback}

Please improve both prompts based on the user's feedback. Preserve the overall structure
and JSON output format requirements, but apply the requested changes."""
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.9,
                max_output_tokens=16384,
                response_mime_type='application/json',
                system_instruction=AGENT_REFINE_META_PROMPT
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=[user_prompt],
                config=config
            )
            
            result = json.loads(response.text)
            
            # Add token usage info
            token_usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                token_usage = {
                    'prompt_tokens': usage.prompt_token_count,
                    'completion_tokens': usage.candidates_token_count,
                    'total_tokens': usage.total_token_count,
                }
            
            result['token_usage'] = token_usage
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prompt refinement response: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error refining prompts: {e}")
            raise
    
    def suggest_queries(self, agent_slug: str) -> Dict[str, Any]:
        """
        Suggest effective Facebook Marketplace search queries for an agent.
        
        Reads the agent's prompts from the database to understand what it 
        looks for, then suggests 3-4 short search terms that would surface
        relevant listings.
        
        Args:
            agent_slug: The slug of the agent to suggest queries for.
        
        Returns:
            Dictionary with 'suggestions' list of query strings.
        """
        if not self.client:
            raise ValueError("API key not configured.")
        
        from apps.scanners.models import Agent as AgentModel
        agent = AgentModel.objects.get(slug=agent_slug, enabled=True)
        
        system_instruction = (
            "You suggest short Facebook Marketplace search queries. "
            "Return JSON: {\"suggestions\": [\"query1\", \"query2\", \"query3\"]}\n"
            "Rules:\n"
            "- 3 to 4 suggestions max\n"
            "- Each query should be 1-4 words, the kind of thing someone types into a search bar\n"
            "- Cover different angles of what the agent looks for\n"
            "- Be specific enough to find relevant listings, broad enough to get results"
        )
        
        user_prompt = (
            f"Agent: {agent.name}\n"
            f"Description: {agent.description}\n\n"
            f"Triage prompt excerpt (first 500 chars):\n{agent.triage_prompt[:500]}\n\n"
            f"What short search queries would find the best listings for this agent?"
        )
        
        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=256,
                response_mime_type='application/json',
                system_instruction=system_instruction
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[user_prompt],
                config=config
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Error suggesting queries: {e}")
            raise
