"""
KaAni GPT API Integration for MAGSASA-CARD ERP
Provides in-app agricultural intelligence without external tabs
"""

import os
from datetime import datetime

import openai
from flask import Blueprint, jsonify, request, session

# Create blueprint for KaAni API routes
kaani_bp = Blueprint("kaani", __name__, url_prefix="/api/kaani")

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

# Role-specific system prompts
SYSTEM_PROMPTS = {
    "farmer": """You are KaAni, a friendly and knowledgeable agricultural advisor specifically designed to help Filipino farmers.

Your expertise includes:
- Rice farming techniques and best practices
- Soil health management and improvement
- Weather-based farming decisions
- Pest and disease identification and treatment
- Crop planning and seasonal timing
- Sustainable farming practices
- Cost-effective farming solutions

Communication style:
- Use simple, clear language that farmers can easily understand
- Be encouraging and supportive
- Provide practical, actionable advice
- Consider the Philippine climate and farming conditions
- Reference local farming practices when relevant
- Always prioritize farmer safety and sustainable practices

When farmers ask questions, provide specific, step-by-step guidance that they can implement immediately on their farms.""",
    "officer": """You are KaAni Agricultural Advisor, a professional agricultural assessment tool for CARD MRI field officers and loan evaluators.

Your expertise includes:
- Agricultural risk assessment and evaluation
- Farm viability analysis for loan applications
- AgScore calculation factors and criteria
- Crop yield estimation and market analysis
- Farming practice evaluation and recommendations
- Financial risk factors in agricultural lending
- Best practices for farm assessment and documentation

Communication style:
- Use professional, technical language appropriate for financial officers
- Provide detailed analysis and reasoning
- Include quantifiable metrics and assessment criteria
- Reference industry standards and best practices
- Focus on risk mitigation and loan security factors
- Provide clear recommendations for loan approval decisions

When conducting assessments, provide comprehensive analysis that supports informed lending decisions while considering agricultural viability and farmer success potential.""",
    "admin": """You are KaAni Agricultural Intelligence, a strategic advisor for CARD MRI administrators and executives.

Your expertise includes:
- Agricultural lending portfolio analysis and optimization
- Market trends and opportunities in Philippine agriculture
- Risk management strategies for agricultural lending
- Strategic planning for agricultural finance expansion
- Competitive analysis and market positioning
- Regulatory compliance and industry best practices
- Business development opportunities in agri-finance

Communication style:
- Use executive-level language and strategic terminology
- Provide high-level insights and strategic recommendations
- Include market data, trends, and competitive intelligence
- Focus on business growth and portfolio optimization
- Reference industry benchmarks and performance metrics
- Provide actionable strategic guidance for decision-making

When providing strategic advice, focus on portfolio performance, market opportunities, and sustainable business growth in the agricultural lending sector.""",
}


def get_user_role():
    """Get the current user's role from session"""
    user_data = session.get("user", {})
    role = user_data.get("role", "farmer")

    # Map roles to KaAni personalities
    role_mapping = {
        "farmer": "farmer",
        "officer": "officer",
        "manager": "officer",
        "admin": "admin",
        "superadmin": "admin",
    }

    return role_mapping.get(role, "farmer")


def get_user_context():
    """Get user-specific context for personalized responses"""
    user_data = session.get("user", {})
    role = get_user_role()

    context = {
        "role": role,
        "username": user_data.get("username", "User"),
        "user_id": user_data.get("id", "unknown"),
    }

    if role == "farmer":
        context.update(
            {
                "farm_type": "rice farming",
                "location": "Philippines",
                "farm_size": "2 hectares",
                "primary_crop": "rice",
            }
        )
    elif role == "officer":
        context.update(
            {
                "organization": "CARD MRI",
                "responsibility": "agricultural loan assessment",
                "focus": "risk evaluation and AgScore calculation",
            }
        )
    elif role == "admin":
        context.update(
            {
                "organization": "CARD MRI",
                "responsibility": "strategic portfolio management",
                "focus": "business development and market analysis",
            }
        )

    return context


@kaani_bp.route("/chat", methods=["POST"])
def chat_with_kaani():
    """Handle chat requests to KaAni GPT"""
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        conversation_history = data.get("history", [])

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Get user role and context
        user_role = get_user_role()
        user_context = get_user_context()

        # Build conversation messages
        messages = [{"role": "system", "content": SYSTEM_PROMPTS[user_role]}]

        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            if isinstance(msg, dict):
                messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )
            elif isinstance(msg, str):
                # Handle string messages as user messages
                messages.append({"role": "user", "content": msg})

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use gpt-3.5-turbo for better compatibility
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Extract response
        kaani_response = response["choices"][0]["message"]["content"]

        # Log the interaction (optional)
        print(f"KaAni Chat - User: {user_context['username']} ({user_role})")
        print(f"Question: {user_message}")
        print(f"Response: {kaani_response[:100]}...")

        return jsonify(
            {
                "success": True,
                "response": kaani_response,
                "role": user_role,
                "context": user_context,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except openai.error.RateLimitError:
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded. Please try again in a moment.",
                    "type": "rate_limit",
                }
            ),
            429,
        )

    except openai.error.InvalidRequestError as e:
        return (
            jsonify({"error": f"Invalid request: {str(e)}", "type": "invalid_request"}),
            400,
        )

    except openai.error.AuthenticationError:
        return (
            jsonify(
                {
                    "error": "Authentication failed. Please check API configuration.",
                    "type": "auth_error",
                }
            ),
            401,
        )

    except Exception as e:
        import traceback

        print(f"KaAni API Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return (
            jsonify(
                {
                    "error": "An unexpected error occurred. Please try again.",
                    "type": "server_error",
                    "debug": str(e) if True else None,  # Enable debug info
                }
            ),
            500,
        )


@kaani_bp.route("/quick-advice", methods=["POST"])
def get_quick_advice():
    """Get quick advice for specific topics"""
    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()

        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        user_role = get_user_role()
        get_user_context()

        # Topic-specific prompts
        topic_prompts = {
            "soil-health": "I need advice on soil health management for my rice farm. What should I check and how can I improve my soil?",
            "weather-advice": "How should I adjust my farming activities based on current weather conditions?",
            "pest-control": "I'm concerned about pests affecting my rice crops. What should I look for and how can I prevent/treat pest problems?",
            "crop-planning": "Help me plan my rice crop schedule and farming activities for the coming season.",
            "field-assessment": "I need to conduct a professional farm assessment for loan evaluation. What factors should I evaluate?",
            "agscore-calculation": "Guide me through calculating AgScore for a farmer loan application. What criteria should I consider?",
            "risk-evaluation": "Help me evaluate agricultural risks for this loan application. What risk factors should I assess?",
            "loan-recommendation": "Based on farm assessment, help me determine loan recommendation criteria and decision factors.",
            "portfolio-analysis": "Provide insights on our agricultural lending portfolio performance and optimization opportunities.",
            "risk-management": "What risk management strategies should we implement for our agricultural lending portfolio?",
            "strategic-planning": "Help me develop strategic plans for expanding our agricultural lending business.",
            "market-insights": "Provide market intelligence and trends for agricultural lending in the Philippines.",
        }

        user_message = topic_prompts.get(topic, f"I need advice about {topic}")

        # Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPTS[user_role]},
            {"role": "user", "content": user_message},
        ]

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages, max_tokens=800, temperature=0.7
        )

        kaani_response = response["choices"][0]["message"]["content"]

        return jsonify(
            {
                "success": True,
                "response": kaani_response,
                "topic": topic,
                "role": user_role,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        print(f"Quick Advice Error: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Failed to get quick advice. Please try again.",
                    "type": "server_error",
                }
            ),
            500,
        )


@kaani_bp.route("/status", methods=["GET"])
def kaani_status():
    """Check KaAni API status"""
    try:
        user_role = get_user_role()
        user_context = get_user_context()

        return jsonify(
            {
                "status": "active",
                "role": user_role,
                "context": user_context,
                "available_features": {
                    "chat": True,
                    "quick_advice": True,
                    "conversation_history": True,
                },
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
