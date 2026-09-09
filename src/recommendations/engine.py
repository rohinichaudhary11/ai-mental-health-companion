"""
Recommendation engine that maps emotions to CBT-based coping strategies.
Provides evidence-based suggestions tailored to each recognized emotion.
"""

import random
from typing import Dict, List, Optional


class RecommendationEngine:
    """Generates personalized recommendations based on detected emotions."""
    
    def __init__(self):
        """Initialize recommendation mappings."""
        self.recommendations = {
            'joy': [
                "Reinforce productive routines; share gratitude with peers.",
                "Celebrate this positive moment and consider journaling about what brought you joy.",
                "Use this energy to engage in activities that align with your values.",
                "Share your positive feelings with someone you trust.",
                "Reflect on what contributed to this joy and how to maintain it."
            ],
            'sadness': [
                "Engage in mindfulness meditation; list three positives daily.",
                "Practice self-compassion and remember that sadness is a valid emotion.",
                "Consider reaching out to a trusted friend or family member.",
                "Engage in gentle physical activity like a short walk.",
                "Write about your feelings in a journal to process them.",
                "Listen to calming music or nature sounds.",
                "Remember that this feeling is temporary and you've overcome difficult times before."
            ],
            'anger': [
                "Apply 4-7-8 breathing technique: inhale for 4, hold for 7, exhale for 8.",
                "Write without sending messages; express your feelings on paper first.",
                "Take a break and step away from the situation if possible.",
                "Practice progressive muscle relaxation.",
                "Engage in physical exercise to release tension.",
                "Use 'I' statements to express your feelings constructively.",
                "Count to ten slowly before responding to triggers."
            ],
            'fear': [
                "Use grounding 5-4-3-2-1 method: identify 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
                "Remind yourself of prior resilience and challenges you've overcome.",
                "Practice deep breathing: inhale for 4 counts, hold for 4, exhale for 4.",
                "Break down the fear into smaller, manageable parts.",
                "Create a safety plan with concrete steps you can take.",
                "Challenge catastrophic thinking by asking 'What's the most likely outcome?'",
                "Remember that fear is a natural response and you have tools to manage it."
            ],
            'disgust': [
                "Reframe your interpretation; focus on acceptance of what you cannot control.",
                "Practice cognitive distancing: observe the feeling without judgment.",
                "Engage in activities that bring you a sense of cleanliness or renewal.",
                "Focus on aspects of the situation you can influence positively.",
                "Use mindfulness to observe the feeling without being consumed by it.",
                "Consider what values are important to you and how to honor them."
            ],
            'surprise': [
                "Take a moment to reflect on what surprised you and why.",
                "Plan adaptive next steps based on this new information.",
                "Allow yourself time to process before making decisions.",
                "Consider both positive and challenging aspects of the surprise.",
                "Reach out to others for perspective if the surprise is significant.",
                "Use this as an opportunity to practice flexibility and adaptability."
            ],
            'stress': [
                "Pause for a few deep breaths and gently relax your shoulders and jaw.",
                "Break tasks into the smallest possible next steps and focus on just one at a time.",
                "Write down what is in your control versus what is outside your control right now.",
                "Schedule a brief recovery break (stretch, short walk, or glass of water) before returning to your tasks.",
                "Practice 4-7-8 breathing and remind yourself that it is okay to slow down.",
                "Reach out to someone you trust and share how overwhelmed you are feeling.",
                "Consider scheduling time with a mental health professional if this level of stress is ongoing."
            ]
        }
        
        # Additional supportive messages
        self.general_support = [
            "Remember, it's okay to feel what you're feeling.",
            "You're taking an important step by acknowledging your emotions.",
            "Every emotion serves a purpose and is valid.",
            "Consider speaking with a mental health professional if these feelings persist.",
            "You have the strength to navigate through this."
        ]
    
    def get_recommendation(self, emotion: str, confidence: Optional[float] = None) -> Dict[str, str]:
        """
        Get a recommendation for a given emotion.
        
        Args:
            emotion: Detected emotion (joy, sadness, anger, fear, disgust, surprise)
            confidence: Confidence score of the prediction (optional)
        
        Returns:
            Dictionary with recommendation and metadata
        """
        emotion = emotion.lower()
        
        if emotion not in self.recommendations:
            # Default recommendation for unknown emotions
            recommendation = random.choice(self.general_support)
        else:
            # Randomly select from available recommendations for this emotion
            recommendation = random.choice(self.recommendations[emotion])
        
        result = {
            'recommendation': recommendation,
            'emotion': emotion,
            'confidence': confidence
        }
        
        # Add additional context based on confidence
        if confidence is not None:
            if confidence < 0.6:
                result['note'] = "The emotion detection had lower confidence. Consider reflecting on multiple possible emotions you might be experiencing."
            elif confidence > 0.9:
                result['note'] = "The emotion was detected with high confidence. This recommendation is specifically tailored to your current emotional state."
        
        return result
    
    def get_multiple_recommendations(self, emotion: str, count: int = 3) -> List[str]:
        """
        Get multiple recommendations for an emotion.
        
        Args:
            emotion: Detected emotion
            count: Number of recommendations to return
        
        Returns:
            List of recommendation strings
        """
        emotion = emotion.lower()
        
        if emotion not in self.recommendations:
            return random.sample(self.general_support, min(count, len(self.general_support)))
        
        available = self.recommendations[emotion].copy()
        if len(available) < count:
            # Supplement with general support if needed
            available.extend(self.general_support)
        
        return random.sample(available, min(count, len(available)))
    
    def add_custom_recommendation(self, emotion: str, recommendation: str):
        """
        Add a custom recommendation for an emotion.
        
        Args:
            emotion: Emotion label
            recommendation: Recommendation text
        """
        emotion = emotion.lower()
        if emotion not in self.recommendations:
            self.recommendations[emotion] = []
        self.recommendations[emotion].append(recommendation)
    
    def get_explanation(self, emotion: str, top_words: List[str] = None) -> str:
        """
        Generate an explanation for why a particular emotion was detected.
        
        Args:
            emotion: Detected emotion
            top_words: List of words that influenced the prediction (optional)
        
        Returns:
            Explanation string
        """
        base_explanations = {
            'joy': "The model detected words indicating happiness, satisfaction, or positive feelings.",
            'sadness': "The model detected words indicating sadness, disappointment, or low mood.",
            'anger': "The model detected words indicating frustration, irritation, or anger.",
            'fear': "The model detected words indicating anxiety, worry, or fear.",
            'disgust': "The model detected words indicating distaste, revulsion, or disgust.",
            'surprise': "The model detected words indicating surprise, shock, or unexpectedness.",
            'stress': "The model detected language about being tense, overwhelmed, or under pressure, which can reflect elevated stress."
        }
        
        explanation = base_explanations.get(emotion.lower(), 
                                          "The model analyzed your text and detected emotional patterns.")
        
        if top_words:
            explanation += f" Key words that influenced this: {', '.join(top_words[:3])}."
        
        return explanation


# Global instance
recommendation_engine = RecommendationEngine()

