"""
Tests for recommendation engine.
"""

import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.recommendations.engine import RecommendationEngine


def test_recommendation_engine_initialization():
    """Test recommendation engine initialization."""
    engine = RecommendationEngine()
    assert engine is not None
    assert 'joy' in engine.recommendations
    assert 'sadness' in engine.recommendations


def test_get_recommendation():
    """Test getting recommendation for an emotion."""
    engine = RecommendationEngine()
    
    result = engine.get_recommendation('joy', confidence=0.9)
    assert 'recommendation' in result
    assert 'emotion' in result
    assert result['emotion'] == 'joy'
    assert len(result['recommendation']) > 0


def test_get_recommendation_all_emotions():
    """Test recommendations for all emotions."""
    engine = RecommendationEngine()
    emotions = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise']
    
    for emotion in emotions:
        result = engine.get_recommendation(emotion)
        assert result['emotion'] == emotion
        assert len(result['recommendation']) > 0


def test_get_explanation():
    """Test explanation generation."""
    engine = RecommendationEngine()
    
    explanation = engine.get_explanation('fear')
    assert len(explanation) > 0
    assert 'fear' in explanation.lower() or 'anxiety' in explanation.lower()


if __name__ == "__main__":
    pytest.main([__file__])

