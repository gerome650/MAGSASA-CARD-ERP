from flask import Blueprint, request, jsonify, session
import openai
import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kaani_assistant_bp = Blueprint('kaani_assistant', __name__)

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')

# KaAni Assistant Instructions (from your GPT)
KAANI_INSTRUCTIONS = """
You are KaAni, a farmer-first assistant specializing in soil, climate, pests, disease, fertility, and finance for agricultural operations in the Philippines.

**CRITICAL EXECUTION PROTOCOL:**
- You, KaAni must first do a sweep with of all of the instructions below and execute which fits best. Do the same for any uploaded file. Identify where the prompts and the uploads belong before proceeding. ALWAYS, ALWAYS begin with this. ALWAYS, ALWAYS begin with this.

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

**CONVERSATION STARTERS:**
- "Kuya, ano magandang abono para sa palay?" (What's good fertilizer for rice?)
- "Ate, anong peste ang dapat bantayan ngayong buwan?" (What pests should we watch for this month?)
- "Paano ko pamamahalaan ang budget sa isang cropping season?" (How do I manage budget for one cropping season?)
- "Safe ba ang pagtatanim ng mais sa lupa kong mabuhangin?" (Is it safe to plant corn in sandy soil?)
"""

# Role-specific customizations
ROLE_CUSTOMIZATIONS = {
    'farmer': {
        'context': 'You are speaking directly to a Filipino farmer. Use simple Tagalog/English mix. Focus on practical, immediate solutions they can implement on their farm.',
        'tone': 'Friendly, encouraging, like a knowledgeable neighbor'},
    'manager': {
        'context': 'You are providing agricultural assessment support to a CARD MRI field manager. Include professional analysis for loan evaluation and risk assessment.',
        'tone': 'Professional but accessible, focus on agricultural expertise for financial decisions'},
    'officer': {
        'context': 'You are assisting a field officer with agricultural evaluation for loan applications. Provide technical assessment and AgScore-relevant insights.',
        'tone': 'Technical and analytical, suitable for loan evaluation reports'},
    'admin': {
        'context': 'You are providing strategic agricultural intelligence for portfolio management and business development.',
        'tone': 'Strategic and comprehensive, focus on market trends and portfolio insights'}}


class KaAniAssistant:
    def __init__(self):
        self.client = openai.OpenAI(api_key=openai.api_key)
        self.assistant_id = None
        self.create_assistant()

    def create_assistant(self):
        """Create or retrieve the KaAni Assistant"""
        try:
            # Try to create a new assistant (in production, you'd store and reuse the assistant_id)
            assistant = self.client.beta.assistants.create(
                name="KaAni Agricultural Advisor",
                description="Farmer-first assistant for soil, climate, pests, disease, fertility, and finance",
                instructions=KAANI_INSTRUCTIONS,
                model="gpt-4-1106-preview",  # Using GPT-4 as closest to GPT-5
                tools=[
                    {"type": "code_interpreter"},
                    {"type": "retrieval"}
                ]
            )
            self.assistant_id = assistant.id
            logger.info(f"Created KaAni Assistant: {self.assistant_id}")
        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            # Fallback to a stored assistant ID if creation fails
            self.assistant_id = "asst_kaani_fallback"

    def get_or_create_thread(self, user_id, role='farmer'):
        """Get existing thread or create new one for user"""
        thread_key = f"kaani_thread_{user_id}_{role}"

        if thread_key in session:
            return session[thread_key]

        try:
            thread = self.client.beta.threads.create()
            session[thread_key] = thread.id
            return thread.id
        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            return None

    def send_message(self, thread_id, message, role='farmer', user_context=None):
        """Send message to KaAni Assistant"""
        try:
            # Add role-specific context to the message
            role_config = ROLE_CUSTOMIZATIONS.get(role, ROLE_CUSTOMIZATIONS['farmer'])

            # Prepare context-enhanced message
            enhanced_message = f"""
ROLE CONTEXT: {role_config['context']}
COMMUNICATION TONE: {role_config['tone']}

USER MESSAGE: {message}
"""

            # Add user context if available
            if user_context:
                enhanced_message = f"""
USER PROFILE: {user_context}

{enhanced_message}
"""

            # Add message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=enhanced_message
            )

            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Wait for completion (simplified - in production, use polling)
            import time
            max_attempts = 30
            attempts = 0

            while attempts < max_attempts:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    logger.error(f"Run failed with status: {run_status.status}")
                    return None

                time.sleep(1)
                attempts += 1

            if attempts >= max_attempts:
                logger.error("Run timed out")
                return None

            # Get the assistant's response
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=1
            )

            if messages.data:
                return messages.data[0].content[0].text.value

            return None

        except Exception as e:
            logger.error(f"Error sending message to assistant: {e}")
            return None


# Initialize the assistant
kaani_assistant = KaAniAssistant()


@kaani_assistant_bp.route('/api/kaani/chat', methods=['POST'])
def chat_with_kaani():
    """Enhanced chat endpoint using Assistant API"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        role = data.get('role', 'farmer')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Get user info from session
        user_id = session.get('user_id', 'anonymous')
        user_name = session.get('user_name', 'User')

        # Prepare user context
        user_context = f"User: {user_name} (Role: {role})"
        if role == 'farmer':
            user_context += " - Filipino farmer seeking agricultural advice"
        elif role == 'manager':
            user_context += " - CARD MRI manager evaluating agricultural loans"
        elif role == 'officer':
            user_context += " - Field officer conducting agricultural assessments"

        # Get or create conversation thread
        thread_id = kaani_assistant.get_or_create_thread(user_id, role)

        if not thread_id:
            return jsonify({'error': 'Failed to create conversation thread'}), 500

        # Send message to KaAni Assistant
        response = kaani_assistant.send_message(
            thread_id=thread_id,
            message=message,
            role=role,
            user_context=user_context
        )

        if not response:
            return jsonify({'error': 'Failed to get response from KaAni'}), 500

        # Log the interaction
        logger.info(f"KaAni Assistant - User: {user_name} ({role}), Message: {message[:50]}...")

        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'thread_id': thread_id,
            'role': role
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@kaani_assistant_bp.route('/api/kaani/quick-advice', methods=['POST'])
def get_quick_advice():
    """Get quick agricultural advice based on category"""
    try:
        data = request.get_json()
        category = data.get('category', '')
        role = data.get('role', 'farmer')

        # Predefined quick advice prompts
        quick_prompts = {
            'soil': 'Paano ko malalaman kung healthy ang lupa ko para sa palay?',
            'weather': 'Anong dapat gawin kapag maulan ngayong season?',
            'pests': 'Anong mga peste ang dapat bantayan ngayong buwan?',
            'crops': 'Kailan ang best time para magtanim ng gulay?',
            'finance': 'Paano ko ma-budget ang gastos sa farming?',
            'assessment': 'What factors should I consider for agricultural loan assessment?',
            'agscore': 'How do I evaluate a farmer\'s agricultural creditworthiness?',
            'risk': 'What are the main agricultural risks to assess?'
        }

        message = quick_prompts.get(category, 'Magbigay ng general farming advice.')

        # Get user info
        user_id = session.get('user_id', 'anonymous')
        user_name = session.get('user_name', 'User')

        # Get or create thread
        thread_id = kaani_assistant.get_or_create_thread(user_id, role)

        if not thread_id:
            return jsonify({'error': 'Failed to create conversation thread'}), 500

        # Get response from KaAni
        response = kaani_assistant.send_message(
            thread_id=thread_id,
            message=message,
            role=role
        )

        if not response:
            return jsonify({'error': 'Failed to get quick advice'}), 500

        return jsonify({
            'response': response,
            'category': category,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in quick advice endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@kaani_assistant_bp.route('/api/kaani/conversation-history', methods=['GET'])
def get_conversation_history():
    """Get conversation history for current user"""
    try:
        user_id = session.get('user_id', 'anonymous')
        role = request.args.get('role', 'farmer')

        thread_id = kaani_assistant.get_or_create_thread(user_id, role)

        if not thread_id:
            return jsonify({'error': 'No conversation found'}), 404

        # Get messages from thread
        messages = kaani_assistant.client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
            limit=50
        )

        conversation = []
        for msg in messages.data:
            conversation.append({
                'role': msg.role,
                'content': msg.content[0].text.value,
                'timestamp': msg.created_at
            })

        return jsonify({
            'conversation': conversation,
            'thread_id': thread_id
        })

    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return jsonify({'error': 'Internal server error'}), 500
