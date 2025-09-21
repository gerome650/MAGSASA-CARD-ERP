"""
Ka-Ani GPT Integration Service
Handles communication with the Ka-Ani GPT API for farmer risk assessment and AgScore calculation
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

class KaAniGPTService:
    def __init__(self):
        # Configuration - these would normally come from environment variables
        self.api_base_url = os.getenv('KA_ANI_API_BASE_URL', 'https://api.kaani.ai/v1')
        self.api_key = os.getenv('KA_ANI_API_KEY', 'demo_key_replace_with_actual')
        self.timeout = 30
        
    def prequalify_farmer(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-qualify a farmer using Ka-Ani GPT
        
        Args:
            farmer_data: Dictionary containing farmer information
            
        Returns:
            Dictionary with pre-qualification results
        """
        try:
            # Prepare the prompt for Ka-Ani GPT
            prompt = self._build_prequalification_prompt(farmer_data)
            
            # Make API call to Ka-Ani GPT
            response = self._call_ka_ani_api('prequalify', {
                'prompt': prompt,
                'farmer_data': farmer_data
            })
            
            if response:
                return {
                    'success': True,
                    'status': response.get('status', 'Unknown'),
                    'recommendations': response.get('recommendations', ''),
                    'confidence_score': response.get('confidence_score', 0.0),
                    'raw_response': response
                }
            else:
                # Fallback to mock response if API is not available
                return self._generate_mock_prequalification(farmer_data)
                
        except Exception as e:
            print(f"Error in Ka-Ani GPT prequalification: {str(e)}")
            return self._generate_mock_prequalification(farmer_data)
    
    def calculate_agscore(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate AgScore for a farmer using Ka-Ani GPT
        
        Args:
            farmer_data: Dictionary containing farmer information
            
        Returns:
            Dictionary with AgScore results
        """
        try:
            # Prepare the prompt for AgScore calculation
            prompt = self._build_agscore_prompt(farmer_data)
            
            # Make API call to Ka-Ani GPT
            response = self._call_ka_ani_api('agscore', {
                'prompt': prompt,
                'farmer_data': farmer_data
            })
            
            if response:
                return {
                    'success': True,
                    'agscore': response.get('agscore', 70),
                    'grade': response.get('grade', 'C'),
                    'risk_factors': response.get('risk_factors', {}),
                    'recommendations': response.get('recommendations', ''),
                    'confidence_score': response.get('confidence_score', 0.0),
                    'raw_response': response
                }
            else:
                # Fallback to mock calculation if API is not available
                return self._calculate_mock_agscore(farmer_data)
                
        except Exception as e:
            print(f"Error in Ka-Ani GPT AgScore calculation: {str(e)}")
            return self._calculate_mock_agscore(farmer_data)
    
    def get_input_recommendations(self, farmer_data: Dict[str, Any], agscore: int) -> Dict[str, Any]:
        """
        Get input recommendations based on farmer data and AgScore
        
        Args:
            farmer_data: Dictionary containing farmer information
            agscore: Farmer's AgScore
            
        Returns:
            Dictionary with input recommendations
        """
        try:
            # Prepare the prompt for input recommendations
            prompt = self._build_input_recommendations_prompt(farmer_data, agscore)
            
            # Make API call to Ka-Ani GPT
            response = self._call_ka_ani_api('input_recommendations', {
                'prompt': prompt,
                'farmer_data': farmer_data,
                'agscore': agscore
            })
            
            if response:
                return {
                    'success': True,
                    'recommendations': response.get('recommendations', []),
                    'total_cost': response.get('total_cost', 0),
                    'loan_recommendation': response.get('loan_recommendation', 0),
                    'raw_response': response
                }
            else:
                # Fallback to mock recommendations if API is not available
                return self._generate_mock_input_recommendations(farmer_data, agscore)
                
        except Exception as e:
            print(f"Error in Ka-Ani GPT input recommendations: {str(e)}")
            return self._generate_mock_input_recommendations(farmer_data, agscore)
    
    def _call_ka_ani_api(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make API call to Ka-Ani GPT service
        
        Args:
            endpoint: API endpoint to call
            data: Data to send in the request
            
        Returns:
            API response or None if failed
        """
        try:
            url = f"{self.api_base_url}/{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Ka-Ani API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Ka-Ani API request failed: {str(e)}")
            return None
    
    def _build_prequalification_prompt(self, farmer_data: Dict[str, Any]) -> str:
        """Build prompt for farmer pre-qualification"""
        name = farmer_data.get('full_name') or farmer_data.get('name', 'Unknown')
        location = farmer_data.get('farm_location_text') or farmer_data.get('location', 'Unknown')
        crop = farmer_data.get('crop_types') or farmer_data.get('crop_type', 'Unknown')
        land_size = farmer_data.get('land_size_ha', 0)
        loan_requested = farmer_data.get('loan_amount_requested', 50000)
        
        return f"""
        Pre-qualify the following farmer for an agricultural loan and input needs based on their data. 
        Provide a 'status' (Pre-qualified, Needs More Info, Not Qualified) and 'recommendations'.
        
        Farmer data:
        - Name: {name}
        - Location: {location}
        - Crop: {crop}
        - Land Size: {land_size} hectares
        - Loan Amount Requested: PHP {loan_requested}
        
        Consider factors like land size, crop type, location, and farming viability.
        """
    
    def _build_agscore_prompt(self, farmer_data: Dict[str, Any]) -> str:
        """Build prompt for AgScore calculation"""
        name = farmer_data.get('full_name') or farmer_data.get('name', 'Unknown')
        location = farmer_data.get('farm_location_text') or farmer_data.get('location', 'Unknown')
        barangay = farmer_data.get('barangay', 'Unknown')
        crop = farmer_data.get('crop_types') or farmer_data.get('crop_type', 'Unknown')
        land_size = farmer_data.get('land_size_ha', 0)
        experience = farmer_data.get('farming_experience', 0)
        
        return f"""
        Calculate an AgScore (0-100) for the following farmer based on agricultural risk assessment.
        Also provide risk factors and recommendations.
        
        Farmer data:
        - Name: {name}
        - Location: {location}
        - Barangay: {barangay}
        - Crop: {crop}
        - Land Size: {land_size} hectares
        - Farming Experience: {experience} years
        
        Consider factors like:
        - Weather risk for the location
        - Soil quality and water availability
        - Crop suitability for the region
        - Market access and infrastructure
        - Farmer experience and land size
        
        Provide AgScore (0-100), grade (A-F), and detailed risk factors.
        """
    
    def _build_input_recommendations_prompt(self, farmer_data: Dict[str, Any], agscore: int) -> str:
        """Build prompt for input recommendations"""
        crop = farmer_data.get('crop_types') or farmer_data.get('crop_type', 'Rice')
        land_size = farmer_data.get('land_size_ha', 1)
        
        return f"""
        Recommend agricultural inputs for a farmer with the following profile:
        - Crop: {crop}
        - Land Size: {land_size} hectares
        - AgScore: {agscore}
        
        Provide specific input recommendations including:
        - Fertilizer types and quantities
        - Seeds/seedlings
        - Pesticides/herbicides if needed
        - Estimated total cost
        - Recommended loan amount
        
        Consider the AgScore when determining input quality and loan risk.
        """
    
    def _generate_mock_prequalification(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock pre-qualification response"""
        land_size = farmer_data.get('land_size_ha', 0)
        experience = farmer_data.get('farming_experience', 0)
        
        # Simple scoring logic for mock response
        if land_size >= 2 and experience >= 3:
            status = 'Pre-qualified'
            recommendations = 'Farmer appears to be a good candidate. Recommend proceeding to full AgScore assessment.'
        elif land_size >= 1 or experience >= 1:
            status = 'Needs More Info'
            recommendations = 'Farmer shows potential but needs additional verification of farming capacity.'
        else:
            status = 'Not Qualified'
            recommendations = 'Farmer may need additional support or training before loan approval.'
        
        return {
            'success': True,
            'status': status,
            'recommendations': recommendations,
            'confidence_score': 0.75,
            'raw_response': {'mock': True}
        }
    
    def _calculate_mock_agscore(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate mock AgScore based on farmer data"""
        base_score = 70
        
        # Adjust score based on land size
        land_size = farmer_data.get('land_size_ha', 0)
        if land_size > 3:
            base_score += 15
        elif land_size > 1:
            base_score += 10
        elif land_size < 0.5:
            base_score -= 10
        
        # Adjust score based on farming experience
        experience = farmer_data.get('farming_experience', 0)
        if experience > 10:
            base_score += 10
        elif experience > 5:
            base_score += 5
        elif experience < 2:
            base_score -= 5
        
        # Adjust score based on crop type
        crop = (farmer_data.get('crop_types') or farmer_data.get('crop_type', '')).lower()
        if 'rice' in crop or 'palay' in crop:
            base_score += 5  # Rice is well-suited for Philippines
        elif 'corn' in crop:
            base_score += 3
        
        # Ensure score is within bounds
        agscore = max(0, min(100, base_score))
        
        # Calculate grade
        if agscore >= 90:
            grade = 'A'
        elif agscore >= 80:
            grade = 'B'
        elif agscore >= 70:
            grade = 'C'
        elif agscore >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        # Generate risk factors
        risk_factors = {
            'weather_risk': 'Low' if agscore > 80 else 'Medium' if agscore > 60 else 'High',
            'soil_quality': 'Good' if land_size > 1 else 'Fair',
            'water_availability': 'Adequate',
            'market_access': 'Good' if farmer_data.get('barangay') else 'Unknown',
            'farmer_experience': 'High' if experience > 5 else 'Medium' if experience > 2 else 'Low'
        }
        
        recommendations = f"AgScore of {agscore} indicates {'low' if agscore > 80 else 'moderate' if agscore > 60 else 'high'} risk. "
        if agscore > 80:
            recommendations += "Excellent candidate for loan approval."
        elif agscore > 60:
            recommendations += "Good candidate with manageable risk."
        else:
            recommendations += "Higher risk candidate - consider additional support or smaller loan amount."
        
        return {
            'success': True,
            'agscore': agscore,
            'grade': grade,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'confidence_score': 0.8,
            'raw_response': {'mock': True}
        }
    
    def _generate_mock_input_recommendations(self, farmer_data: Dict[str, Any], agscore: int) -> Dict[str, Any]:
        """Generate mock input recommendations"""
        land_size = farmer_data.get('land_size_ha', 1)
        crop = (farmer_data.get('crop_types') or farmer_data.get('crop_type', 'rice')).lower()
        
        recommendations = []
        total_cost = 0
        
        if 'rice' in crop or 'palay' in crop:
            # Rice farming inputs
            fertilizer_bags = max(1, int(land_size * 6))  # 6 bags per hectare
            seed_kg = max(1, int(land_size * 40))  # 40kg per hectare
            
            recommendations.extend([
                {
                    'item': 'Complete Fertilizer (14-14-14)',
                    'quantity': fertilizer_bags,
                    'unit': 'bags',
                    'unit_cost': 1200,
                    'total_cost': fertilizer_bags * 1200
                },
                {
                    'item': 'Urea Fertilizer',
                    'quantity': max(1, fertilizer_bags // 2),
                    'unit': 'bags',
                    'unit_cost': 1100,
                    'total_cost': max(1, fertilizer_bags // 2) * 1100
                },
                {
                    'item': 'Rice Seeds (Certified)',
                    'quantity': seed_kg,
                    'unit': 'kg',
                    'unit_cost': 45,
                    'total_cost': seed_kg * 45
                }
            ])
        else:
            # Generic crop inputs
            fertilizer_bags = max(1, int(land_size * 4))
            
            recommendations.extend([
                {
                    'item': 'Complete Fertilizer',
                    'quantity': fertilizer_bags,
                    'unit': 'bags',
                    'unit_cost': 1200,
                    'total_cost': fertilizer_bags * 1200
                },
                {
                    'item': 'Organic Fertilizer',
                    'quantity': max(1, fertilizer_bags // 2),
                    'unit': 'bags',
                    'unit_cost': 800,
                    'total_cost': max(1, fertilizer_bags // 2) * 800
                }
            ])
        
        # Calculate total cost
        total_cost = sum(item['total_cost'] for item in recommendations)
        
        # Adjust loan recommendation based on AgScore
        if agscore >= 80:
            loan_recommendation = int(total_cost * 1.2)  # 120% of input cost
        elif agscore >= 60:
            loan_recommendation = int(total_cost * 1.1)  # 110% of input cost
        else:
            loan_recommendation = int(total_cost * 1.0)  # 100% of input cost
        
        return {
            'success': True,
            'recommendations': recommendations,
            'total_cost': total_cost,
            'loan_recommendation': loan_recommendation,
            'raw_response': {'mock': True}
        }

# Global instance
ka_ani_service = KaAniGPTService()

