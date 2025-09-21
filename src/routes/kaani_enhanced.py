"""
Enhanced KaAni Assistant Implementation
Uses available models with Assistant-like functionality
"""

from flask import Blueprint, request, jsonify, session
import openai
import os
import json
import logging
from datetime import datetime
import uuid
import re
from src.kaani_functions import execute_kaani_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kaani_enhanced_bp = Blueprint('kaani_enhanced', __name__)

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')

# KaAni's Enhanced Instructions
KAANI_SYSTEM_PROMPT = """
You are KaAni, a farmer-first assistant specializing in soil, climate, pests, disease, fertility, and finance for agricultural operations in the Philippines.

**CRITICAL EXECUTION PROTOCOL:**
- You, KaAni must first do a sweep with of all of the instructions below and execute which fits best. Do the same for any uploaded file. Identify where the prompts and the uploads belong before proceeding. ALWAYS, ALWAYS begin with this.

**SPECIALIZED RESPONSE PROTOCOLS:**

*ALL PROMPTS PERTAINING to SOIL and CLIMATE, PESTS, DISEASE, FERTILIZATION please refer to the COMPRESSED ACTIONS SECTION OF THE FIRM INSTRUCTIONS FILE. Avoid using English Technical terms for the farmer.

*For PESTS include Phenological pest pressure and chemical actions in the response.
*For CROPS do a weighted analysis of the sentence, see what the context of the question is that pertains to crops. Enter the file of the context that bears more weight.
*if a chart, file, and/or prompts that concern Satellite data is submitted REFER to the SATELLITE file. There are sample charts (png and csv) in the KB. Remember Farmer Friendly. Simple Composite = steps #1 - #8 in handbook, Stage weighed = steps #1 - #11.

*Remember that if the word Risk is mentioned by the user without any additional context, it has to be determined first what type of risk he is referring to.

**SCOPE LIMITATION:**
You should only be asked questions pertaining to crop farming and farmer financial literacy. Anything outside that you should only reply that you are a specialized language model tailored for crop/vegetable farming.

**COMMUNICATION STYLE:**
- Use simple, farmer-friendly language
- Avoid complex English technical terms
- Provide practical, actionable advice
- Include local context for Philippines agriculture
- Be encouraging and supportive
- Mix Tagalog and English naturally (Taglish) when appropriate
- Use "Kuya" or "Ate" as respectful address terms

**CONVERSATION STARTERS:**
- "Kuya, ano magandang abono para sa palay?" (What's good fertilizer for rice?)
- "Ate, anong peste ang dapat bantayan ngayong buwan?" (What pests should we watch for this month?)
- "Paano ko pamamahalaan ang budget sa isang cropping season?" (How do I manage budget for one cropping season?)
- "Safe ba ang pagtatanim ng mais sa lupa kong mabuhangin?" (Is it safe to plant corn in sandy soil?)

**AGRICULTURAL EXPERTISE AREAS:**
1. **Soil Management**: pH testing, nutrient analysis, soil improvement techniques
2. **Climate Adaptation**: Weather-based farming decisions, seasonal planning
3. **Pest & Disease Control**: Identification, prevention, treatment methods
4. **Crop Planning**: Planting schedules, variety selection, rotation strategies
5. **Financial Literacy**: Budget planning, loan management, cost optimization
6. **Risk Assessment**: Agricultural risks, mitigation strategies, insurance options

**PHILIPPINES-SPECIFIC KNOWLEDGE:**
- Local farming practices and traditions
- Philippine climate patterns and seasons (wet/dry seasons)
- Common crops: rice (palay), corn (mais), vegetables
- Local pest and disease pressures
- CARD MRI lending practices and requirements
- AgScore evaluation criteria
- Local market conditions and pricing

**RESPONSE FORMAT:**
Always structure responses with:
1. Acknowledgment of the question
2. Clear, actionable advice
3. Specific steps or recommendations
4. Local context when relevant
5. Encouragement and support

Remember: You are here to empower Filipino farmers with knowledge and support their success in agriculture and financial management.
"""

# Role-specific customizations
ROLE_CUSTOMIZATIONS = {
    'farmer': {
        'context': 'You are speaking directly to a Filipino farmer. Use simple Tagalog/English mix. Focus on practical, immediate solutions they can implement on their farm.',
        'tone': 'Friendly, encouraging, like a knowledgeable neighbor',
        'greeting': 'Kumusta, Kuya/Ate! Ako si KaAni, ang inyong agricultural advisor. Ano ang maitutulong ko sa inyong farm ngayon?'
    },
    'manager': {
        'context': 'You are providing agricultural assessment support to a CARD MRI field manager. Include professional analysis for loan evaluation and risk assessment.',
        'tone': 'Professional but accessible, focus on agricultural expertise for financial decisions',
        'greeting': 'Hello! I\'m KaAni, your agricultural advisor. I can help with farm assessments, AgScore evaluation, and agricultural risk analysis for loan decisions.'
    },
    'officer': {
        'context': 'You are assisting a field officer with agricultural evaluation for loan applications. Provide technical assessment and AgScore-relevant insights.',
        'tone': 'Technical and analytical, suitable for loan evaluation reports',
        'greeting': 'Good day! I\'m KaAni, ready to assist with agricultural assessments and loan evaluation criteria. How can I help with your field work today?'
    },
    'admin': {
        'context': 'You are providing strategic agricultural intelligence for portfolio management and business development.',
        'tone': 'Strategic and comprehensive, focus on market trends and portfolio insights',
        'greeting': 'Welcome! I\'m KaAni, your agricultural intelligence advisor. I can provide strategic insights for portfolio management and agricultural lending decisions.'
    }
}

class EnhancedKaAniAssistant:
    def __init__(self):
        # Initialize OpenAI with API key
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.conversations = {}  # Store conversation threads
        
    def get_available_model(self):
        """Get the best available model"""
        # Based on the error, these are the available models
        available_models = ['gpt-4.1-mini', 'gpt-4.1-nano', 'gemini-2.5-flash']
        return available_models[0]  # Use gpt-4.1-mini as primary
    
    def get_or_create_thread(self, user_id, role='farmer'):
        """Get existing conversation thread or create new one"""
        thread_key = f"{user_id}_{role}"
        
        if thread_key not in self.conversations:
            self.conversations[thread_key] = {
                'id': str(uuid.uuid4()),
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'role': role,
                'user_id': user_id
            }
            
            # Add initial greeting
            role_config = ROLE_CUSTOMIZATIONS.get(role, ROLE_CUSTOMIZATIONS['farmer'])
            greeting = role_config['greeting']
            
            self.conversations[thread_key]['messages'].append({
                'role': 'assistant',
                'content': greeting,
                'timestamp': datetime.now().isoformat()
            })
        
        return self.conversations[thread_key]
    
    def send_message(self, thread_id, message, role='farmer', user_context=None):
        """Send message to KaAni and get response"""
        try:
            # Find the conversation thread
            thread = None
            for conv in self.conversations.values():
                if conv['id'] == thread_id:
                    thread = conv
                    break
            
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return None
            
            # Add user message to thread
            thread['messages'].append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Prepare role-specific context
            role_config = ROLE_CUSTOMIZATIONS.get(role, ROLE_CUSTOMIZATIONS['farmer'])
            
            # Build conversation messages for API
            api_messages = [
                {"role": "system", "content": f"{KAANI_SYSTEM_PROMPT}\n\nROLE CONTEXT: {role_config['context']}\nCOMMUNICATION TONE: {role_config['tone']}"}
            ]
            
            # Add conversation history (last 10 messages)
            recent_messages = thread['messages'][-10:]
            for msg in recent_messages:
                if msg['role'] in ['user', 'assistant']:
                    api_messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
            
            # Add current user message if not already included
            if not any(msg['role'] == 'user' and msg['content'] == message for msg in api_messages[-3:]):
                api_messages.append({
                    "role": "user",
                    "content": message
                })
            
            # Check if function calling is needed
            function_data = self.detect_function_call(message, role)
            
            if function_data:
                # Execute function and add result to context
                function_result = execute_kaani_function(
                    function_data['function'],
                    **function_data['parameters']
                )
                
                # Add function result to messages
                api_messages.append({
                    "role": "system",
                    "content": f"FUNCTION RESULT for {function_data['function']}: {json.dumps(function_result, indent=2)}\n\nUse this data to provide a comprehensive answer to the user's question."
                })
            
            # Call OpenAI API (using older version syntax)
            response = openai.ChatCompletion.create(
                model=self.get_available_model(),
                messages=api_messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract response (older version syntax)
            kaani_response = response['choices'][0]['message']['content']
            
            # Add assistant response to thread
            thread['messages'].append({
                'role': 'assistant',
                'content': kaani_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 messages to manage memory
            if len(thread['messages']) > 50:
                thread['messages'] = thread['messages'][-50:]
            
            return kaani_response
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return None
    
    def detect_function_call(self, message, role):
        """Detect if a message requires function calling"""
        message_lower = message.lower()
        
        # Function detection patterns
        patterns = {
            'get_farmer_profile': [
                r'profile', r'information', r'details', r'about me', r'my farm',
                r'sino ako', r'tungkol sa akin', r'farm ko'
            ],
            'get_farmer_orders': [
                r'orders', r'purchases', r'bought', r'history', r'binili',
                r'mga order', r'naorder', r'inputs'
            ],
            'get_seasonal_recommendations': [
                r'season', r'plant', r'crop', r'timing', r'kailan', r'season',
                r'panahon', r'magtanim'
            ],
            'calculate_input_needs': [
                r'fertilizer', r'inputs', r'needs', r'calculate', r'budget',
                r'abono', r'pangangailangan', r'gastos', r'magkano'
            ],
            'get_weather_advice': [
                r'weather', r'rain', r'climate', r'panahon', r'ulan',
                r'temperatura', r'season advice'
            ],
            'prequalify_farmer': [
                r'prequalify', r'pre-qualify', r'loan assessment', r'evaluate',
                r'agscore', r'qualification', r'loan application', r'assess farmer'
            ]
        }
        
        # Check for function patterns
        for function_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, message_lower):
                    # Extract parameters based on function type
                    parameters = self.extract_parameters(message, function_name)
                    return {
                        'function': function_name,
                        'parameters': parameters
                    }
        
        return None
    
    def extract_parameters(self, message, function_name):
        """Extract parameters from message for function calling"""
        parameters = {}
        message_lower = message.lower()
        
        # Extract common parameters
        if function_name == 'calculate_input_needs':
            # Look for farm size
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hectare|ha|ektarya)', message_lower)
            if size_match:
                parameters['farm_size'] = float(size_match.group(1))
            
            # Look for crop type
            if any(crop in message_lower for crop in ['rice', 'palay']):
                parameters['crop_type'] = 'rice'
            elif any(crop in message_lower for crop in ['corn', 'mais']):
                parameters['crop_type'] = 'corn'
            elif any(crop in message_lower for crop in ['vegetable', 'gulay']):
                parameters['crop_type'] = 'vegetables'
        
        elif function_name == 'get_seasonal_recommendations':
            # Extract crop type
            if any(crop in message_lower for crop in ['rice', 'palay']):
                parameters['crop_type'] = 'rice'
            elif any(crop in message_lower for crop in ['corn', 'mais']):
                parameters['crop_type'] = 'corn'
        
        elif function_name == 'prequalify_farmer':
            # Extract farmer details from message
            # Look for name
            name_match = re.search(r'(?:farmer|name|pangalan)\s*:?\s*([a-zA-Z\s]+)', message_lower)
            if name_match:
                parameters['farmer_name'] = name_match.group(1).strip().title()
            
            # Look for location
            location_match = re.search(r'(?:location|lugar|address)\s*:?\s*([a-zA-Z\s,]+)', message_lower)
            if location_match:
                parameters['location'] = location_match.group(1).strip().title()
            
            # Look for crop
            if any(crop in message_lower for crop in ['rice', 'palay']):
                parameters['crop'] = 'rice'
            elif any(crop in message_lower for crop in ['corn', 'mais']):
                parameters['crop'] = 'corn'
            elif any(crop in message_lower for crop in ['vegetable', 'gulay']):
                parameters['crop'] = 'vegetables'
            
            # Look for land size
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hectare|ha|ektarya)', message_lower)
            if size_match:
                parameters['land_size_ha'] = float(size_match.group(1))
            
            # Look for loan amount
            amount_match = re.search(r'(?:loan|amount|halaga)\s*:?\s*(?:php\s*)?(\d+(?:,\d+)*)', message_lower)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                parameters['loan_amount_requested'] = float(amount_str)
        
        return parameters
    
    def get_conversation_history(self, thread_id):
        """Get conversation history for a thread"""
        for conv in self.conversations.values():
            if conv['id'] == thread_id:
                return conv['messages']
        return []

# Initialize the enhanced assistant
kaani_enhanced = EnhancedKaAniAssistant()

@kaani_enhanced_bp.route('/api/kaani/chat', methods=['POST'])
def enhanced_chat():
    """Enhanced chat endpoint with thread management"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        role = data.get('role', 'farmer')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user info from session
        user_id = session.get('user_id', 'anonymous')
        user_name = session.get('user_name', 'User')
        
        # Get or create conversation thread
        thread = kaani_enhanced.get_or_create_thread(user_id, role)
        
        # Send message to KaAni
        response = kaani_enhanced.send_message(
            thread_id=thread['id'],
            message=message,
            role=role,
            user_context=f"User: {user_name} (Role: {role})"
        )
        
        if not response:
            return jsonify({'error': 'Failed to get response from KaAni'}), 500
        
        # Log the interaction
        logger.info(f"Enhanced KaAni - User: {user_name} ({role}), Message: {message[:50]}...")
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'thread_id': thread['id'],
            'role': role,
            'conversation_length': len(thread['messages'])
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@kaani_enhanced_bp.route('/api/kaani/quick-advice', methods=['POST'])
def enhanced_quick_advice():
    """Enhanced quick advice with role-specific prompts"""
    try:
        data = request.get_json()
        category = data.get('category', '')
        role = data.get('role', 'farmer')
        
        # Role-specific quick advice prompts
        quick_prompts = {
            'farmer': {
                'soil': 'Kuya, paano ko malalaman kung healthy ang lupa ko para sa palay? Anong mga signs ang dapat tignan?',
                'weather': 'Ate, anong dapat gawin kapag maulan ngayong season? Paano ko ma-protect ang crops ko?',
                'pests': 'Kuya, anong mga peste ang dapat bantayan ngayong buwan sa palay? Paano ko sila mapipigilan?',
                'crops': 'Ate, kailan ang best time para magtanim ng gulay? Anong varieties ang maganda?',
                'finance': 'Kuya, paano ko ma-budget ang gastos sa farming? Anong mga tips para sa pera?'
            },
            'officer': {
                'assessment': 'What factors should I evaluate when conducting a farm assessment for loan applications?',
                'agscore': 'Guide me through calculating AgScore for a farmer loan application. What criteria are most important?',
                'risk': 'What are the main agricultural risks I should assess for loan evaluation?',
                'documentation': 'What documentation and evidence should I collect during farm visits?'
            },
            'manager': {
                'portfolio': 'What agricultural factors should I consider for portfolio risk management?',
                'approval': 'What agricultural criteria should guide loan approval decisions?',
                'monitoring': 'How should I monitor agricultural loan performance and farmer success?'
            },
            'admin': {
                'strategy': 'What strategic opportunities exist in agricultural lending in the Philippines?',
                'market': 'What are the current market trends in agricultural finance?',
                'expansion': 'How can we expand our agricultural lending portfolio effectively?'
            }
        }
        
        role_prompts = quick_prompts.get(role, quick_prompts['farmer'])
        message = role_prompts.get(category, 'Magbigay ng general farming advice.')
        
        # Get user info
        user_id = session.get('user_id', 'anonymous')
        
        # Get or create thread
        thread = kaani_enhanced.get_or_create_thread(user_id, role)
        
        # Get response from KaAni
        response = kaani_enhanced.send_message(
            thread_id=thread['id'],
            message=message,
            role=role
        )
        
        if not response:
            return jsonify({'error': 'Failed to get quick advice'}), 500
        
        return jsonify({
            'success': True,
            'response': response,
            'category': category,
            'role': role,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced quick advice endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@kaani_enhanced_bp.route('/api/kaani/conversation-history', methods=['GET'])
def enhanced_conversation_history():
    """Get conversation history for current user"""
    try:
        user_id = session.get('user_id', 'anonymous')
        role = request.args.get('role', 'farmer')
        
        thread = kaani_enhanced.get_or_create_thread(user_id, role)
        
        return jsonify({
            'success': True,
            'conversation': thread['messages'],
            'thread_id': thread['id'],
            'role': role,
            'created_at': thread['created_at']
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@kaani_enhanced_bp.route('/api/kaani/status', methods=['GET'])
def enhanced_status():
    """Enhanced KaAni status with model information"""
    try:
        user_role = session.get('user', {}).get('role', 'farmer')
        
        return jsonify({
            'status': 'active',
            'version': 'enhanced_v1.0',
            'model': kaani_enhanced.get_available_model(),
            'role': user_role,
            'features': {
                'conversation_threading': True,
                'role_based_responses': True,
                'quick_advice': True,
                'conversation_history': True,
                'agricultural_expertise': True,
                'filipino_context': True
            },
            'active_conversations': len(kaani_enhanced.conversations)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
