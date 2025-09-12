"""
Real-time Collaboration Heatmap Analysis Engine
Generates contextual insights from interaction data and quiz performance metrics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy import func, and_
from app import db
from models import (
    InteractionEvent, QuestionHeatmapData, CollaborationInsight, 
    QuizAttempt, Question, Answer, Quiz
)

class HeatmapAnalysisEngine:
    """Engine for analyzing heatmap data and generating contextual insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_quiz_performance(self, quiz_id: int) -> List[Dict[str, Any]]:
        """
        Analyze overall quiz performance and generate insights
        
        Args:
            quiz_id: ID of the quiz to analyze
            
        Returns:
            List of generated insights
        """
        insights = []
        
        try:
            # Get quiz and basic metrics
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return insights
            
            # Analyze different aspects
            insights.extend(self._analyze_difficulty_patterns(quiz_id))
            insights.extend(self._analyze_engagement_patterns(quiz_id))
            insights.extend(self._analyze_confusion_areas(quiz_id))
            insights.extend(self._analyze_performance_trends(quiz_id))
            insights.extend(self._analyze_interaction_hotspots(quiz_id))
            
            # Save insights to database
            for insight_data in insights:
                self._save_insight(quiz_id, insight_data)
                
        except Exception as e:
            self.logger.error(f"Error analyzing quiz {quiz_id}: {e}")
        
        return insights
    
    def _analyze_difficulty_patterns(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Identify questions with difficulty patterns"""
        insights = []
        
        try:
            # Get heatmap data for all questions
            heatmap_data = QuestionHeatmapData.query.filter_by(quiz_id=quiz_id).all()
            
            if not heatmap_data:
                return insights
            
            # Identify difficult questions (low correct rate + high interaction time)
            difficult_questions = []
            for data in heatmap_data:
                if (data.correct_answer_rate < 50 and 
                    data.average_time_spent > 0 and
                    data.total_participants > 0):
                    difficult_questions.append({
                        'questionId': data.question_id,
                        'correctRate': data.correct_answer_rate,
                        'avgTime': data.average_time_spent,
                        'participants': data.total_participants
                    })
            
            if difficult_questions:
                # Sort by difficulty (lowest correct rate first)
                difficult_questions.sort(key=lambda x: x['correctRate'])
                worst_questions = difficult_questions[:3]  # Top 3 most difficult
                
                severity = 'high' if len(difficult_questions) > 3 else 'medium'
                
                insights.append({
                    'type': 'difficulty_pattern',
                    'title': f'{len(difficult_questions)} Questions Show High Difficulty',
                    'description': f'Multiple questions have low success rates (<50%) and high completion times. Students are struggling with specific content areas.',
                    'severity': severity,
                    'affected_questions': [q['questionId'] for q in difficult_questions],
                    'metric_values': {
                        'total_difficult': len(difficult_questions),
                        'worst_questions': worst_questions,
                        'avg_correct_rate': sum(q['correctRate'] for q in difficult_questions) / len(difficult_questions)
                    },
                    'suggested_actions': [
                        'Review question wording for clarity',
                        'Consider additional hints or examples',
                        'Provide prerequisite materials',
                        'Schedule review session for difficult topics'
                    ]
                })
                
        except Exception as e:
            self.logger.error(f"Error analyzing difficulty patterns: {e}")
        
        return insights
    
    def _analyze_engagement_patterns(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Analyze participant engagement patterns"""
        insights = []
        
        try:
            # Get interaction events for engagement analysis
            attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
            if not attempts:
                return insights
            
            attempt_ids = [attempt.id for attempt in attempts]
            
            # Analyze engagement drops over time
            events = db.session.query(InteractionEvent).filter(
                InteractionEvent.attempt_id.in_(attempt_ids)
            ).order_by(InteractionEvent.timestamp).all()
            
            if events:
                # Group events by time windows (5-minute intervals)
                time_windows = self._group_events_by_time_windows(events, minutes=5)
                
                # Look for significant engagement drops
                engagement_drops = []
                for i in range(1, len(time_windows)):
                    current = len(time_windows[i])
                    previous = len(time_windows[i-1])
                    
                    if previous > 0:
                        drop_percentage = ((previous - current) / previous) * 100
                        if drop_percentage > 30:  # 30% drop threshold
                            engagement_drops.append({
                                'window': i,
                                'drop_percentage': drop_percentage,
                                'events_before': previous,
                                'events_after': current
                            })
                
                if engagement_drops:
                    worst_drop = max(engagement_drops, key=lambda x: x['drop_percentage'])
                    
                    insights.append({
                        'type': 'engagement_drop',
                        'title': f'Engagement Drop Detected ({worst_drop["drop_percentage"]:.1f}%)',
                        'description': f'Significant decrease in participant interactions detected during the quiz session.',
                        'severity': 'medium' if worst_drop['drop_percentage'] < 50 else 'high',
                        'affected_questions': [],  # Time-based, not question-specific
                        'metric_values': {
                            'total_drops': len(engagement_drops),
                            'worst_drop': worst_drop,
                            'total_events': len(events)
                        },
                        'suggested_actions': [
                            'Check quiz length and pacing',
                            'Consider adding breaks or checkpoints',
                            'Review content difficulty progression',
                            'Monitor participant fatigue indicators'
                        ]
                    })
                    
        except Exception as e:
            self.logger.error(f"Error analyzing engagement patterns: {e}")
        
        return insights
    
    def _analyze_confusion_areas(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Identify areas where participants show confusion"""
        insights = []
        
        try:
            # Get questions with high interaction but low accuracy
            heatmap_data = QuestionHeatmapData.query.filter_by(quiz_id=quiz_id).all()
            
            confusion_indicators = []
            for data in heatmap_data:
                if data.total_participants > 0:
                    # High interaction density with low accuracy indicates confusion
                    interaction_density = (data.total_clicks + data.total_hovers) / data.total_participants
                    
                    if (interaction_density > 10 and  # High interaction
                        data.correct_answer_rate < 60 and  # Low accuracy
                        data.average_time_spent > 0):
                        
                        confusion_score = interaction_density * (100 - data.correct_answer_rate) / 100
                        confusion_indicators.append({
                            'questionId': data.question_id,
                            'confusion_score': confusion_score,
                            'interaction_density': interaction_density,
                            'correct_rate': data.correct_answer_rate,
                            'avg_time': data.average_time_spent
                        })
            
            if confusion_indicators:
                # Sort by confusion score
                confusion_indicators.sort(key=lambda x: x['confusion_score'], reverse=True)
                top_confusion = confusion_indicators[:2]  # Top 2 most confusing
                
                insights.append({
                    'type': 'confusion_area',
                    'title': f'{len(confusion_indicators)} Questions Show Confusion Patterns',
                    'description': 'High interaction activity combined with low accuracy suggests participant confusion.',
                    'severity': 'medium',
                    'affected_questions': [q['questionId'] for q in confusion_indicators],
                    'metric_values': {
                        'total_confused': len(confusion_indicators),
                        'top_confusion': top_confusion,
                        'avg_confusion_score': sum(q['confusion_score'] for q in confusion_indicators) / len(confusion_indicators)
                    },
                    'suggested_actions': [
                        'Clarify question instructions',
                        'Review answer option wording',
                        'Add visual aids or examples',
                        'Consider question redesign'
                    ]
                })
                
        except Exception as e:
            self.logger.error(f"Error analyzing confusion areas: {e}")
        
        return insights
    
    def _analyze_performance_trends(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Analyze performance trends across the quiz"""
        insights = []
        
        try:
            # Get questions in order and their performance
            questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id).all()
            if len(questions) < 3:  # Need at least 3 questions for trends
                return insights
            
            # Get performance data for each question
            performance_data = []
            for question in questions:
                heatmap = QuestionHeatmapData.query.filter_by(
                    quiz_id=quiz_id, 
                    question_id=question.id
                ).first()
                
                if heatmap and heatmap.total_participants > 0:
                    performance_data.append({
                        'questionId': question.id,
                        'position': len(performance_data) + 1,
                        'correct_rate': heatmap.correct_answer_rate,
                        'avg_time': heatmap.average_time_spent,
                        'engagement': heatmap.engagement_score
                    })
            
            if len(performance_data) >= 3:
                # Analyze trends
                trends = self._calculate_performance_trends(performance_data)
                
                for trend in trends:
                    if trend['significant']:
                        insights.append({
                            'type': 'performance_trend',
                            'title': f'{trend["type"].title()} Performance Trend Detected',
                            'description': trend['description'],
                            'severity': 'low',
                            'affected_questions': [q['questionId'] for q in performance_data],
                            'metric_values': {
                                'trend_type': trend['type'],
                                'trend_strength': trend['strength'],
                                'performance_data': performance_data
                            },
                            'suggested_actions': trend['suggestions']
                        })
                        
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {e}")
        
        return insights
    
    def _analyze_interaction_hotspots(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Analyze interaction hotspots for UX insights"""
        insights = []
        
        try:
            # Get questions with hotspot data
            heatmap_data = QuestionHeatmapData.query.filter_by(quiz_id=quiz_id).all()
            
            hotspot_insights = []
            for data in heatmap_data:
                if data.click_hotspots and data.total_participants > 5:  # Need sufficient data
                    hotspots = json.loads(data.click_hotspots)
                    
                    if len(hotspots) > 0:
                        # Analyze hotspot distribution
                        hotspot_analysis = self._analyze_hotspot_distribution(hotspots)
                        
                        if hotspot_analysis['concentrated']:
                            hotspot_insights.append({
                                'questionId': data.question_id,
                                'hotspot_analysis': hotspot_analysis,
                                'total_clicks': data.total_clicks,
                                'participants': data.total_participants
                            })
            
            if hotspot_insights:
                insights.append({
                    'type': 'interaction_hotspot',
                    'title': f'Interaction Hotspots Identified in {len(hotspot_insights)} Questions',
                    'description': 'Concentrated click patterns suggest specific UI elements or content areas draw attention.',
                    'severity': 'low',
                    'affected_questions': [h['questionId'] for h in hotspot_insights],
                    'metric_values': {
                        'hotspot_questions': len(hotspot_insights),
                        'hotspot_details': hotspot_insights
                    },
                    'suggested_actions': [
                        'Review UI element placement',
                        'Analyze content layout effectiveness',
                        'Consider A/B testing different designs',
                        'Monitor user experience patterns'
                    ]
                })
                
        except Exception as e:
            self.logger.error(f"Error analyzing interaction hotspots: {e}")
        
        return insights
    
    def _group_events_by_time_windows(self, events: List[InteractionEvent], minutes: int = 5) -> List[List]:
        """Group events into time windows"""
        if not events:
            return []
        
        windows = []
        current_window = []
        window_start = events[0].timestamp
        window_duration = timedelta(minutes=minutes)
        
        for event in events:
            if event.timestamp - window_start <= window_duration:
                current_window.append(event)
            else:
                windows.append(current_window)
                current_window = [event]
                window_start = event.timestamp
        
        if current_window:
            windows.append(current_window)
        
        return windows
    
    def _calculate_performance_trends(self, performance_data: List[Dict]) -> List[Dict]:
        """Calculate performance trends across questions"""
        trends = []
        
        if len(performance_data) < 3:
            return trends
        
        # Analyze correct rate trend
        correct_rates = [p['correct_rate'] for p in performance_data]
        correct_trend = self._calculate_trend(correct_rates)
        
        if abs(correct_trend) > 0.3:  # Significant trend threshold
            trend_type = 'declining' if correct_trend < 0 else 'improving'
            trends.append({
                'type': f'{trend_type}_accuracy',
                'strength': abs(correct_trend),
                'significant': True,
                'description': f'Accuracy {trend_type} throughout the quiz (trend: {correct_trend:.2f})',
                'suggestions': [
                    'Review question ordering',
                    'Consider difficulty progression',
                    'Monitor fatigue effects'
                ] if trend_type == 'declining' else [
                    'Maintain current progression',
                    'Use as template for future quizzes'
                ]
            })
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend coefficient"""
        n = len(values)
        if n < 2:
            return 0
        
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0
    
    def _analyze_hotspot_distribution(self, hotspots: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Analyze if hotspots are concentrated or distributed"""
        if len(hotspots) < 5:
            return {'concentrated': False}
        
        # Calculate clustering (simplified approach)
        x_coords = [h[0] for h in hotspots if h[0] is not None]
        y_coords = [h[1] for h in hotspots if h[1] is not None]
        
        if not x_coords or not y_coords:
            return {'concentrated': False}
        
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        # If most clicks are in a small area, consider it concentrated
        x_concentrated = x_range < 200  # pixels
        y_concentrated = y_range < 200  # pixels
        
        return {
            'concentrated': x_concentrated and y_concentrated,
            'x_range': x_range,
            'y_range': y_range,
            'total_hotspots': len(hotspots)
        }
    
    def _save_insight(self, quiz_id: int, insight_data: Dict[str, Any]) -> None:
        """Save insight to database"""
        try:
            # Check if similar insight already exists
            existing = CollaborationInsight.query.filter_by(
                quiz_id=quiz_id,
                insight_type=insight_data['type'],
                is_active=True
            ).first()
            
            if existing:
                # Update existing insight
                existing.title = insight_data['title']
                existing.description = insight_data['description']
                existing.severity = insight_data['severity']
                existing.affected_questions = json.dumps(insight_data['affected_questions'])
                existing.metric_values = json.dumps(insight_data['metric_values'])
                existing.suggested_actions = json.dumps(insight_data['suggested_actions'])
                existing.updated_at = datetime.utcnow()
            else:
                # Create new insight
                insight = CollaborationInsight(
                    quiz_id=quiz_id,
                    insight_type=insight_data['type'],
                    title=insight_data['title'],
                    description=insight_data['description'],
                    severity=insight_data['severity'],
                    affected_questions=json.dumps(insight_data['affected_questions']),
                    metric_values=json.dumps(insight_data['metric_values']),
                    suggested_actions=json.dumps(insight_data['suggested_actions'])
                )
                db.session.add(insight)
            
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error saving insight: {e}")
            db.session.rollback()

# Global analysis engine instance
analysis_engine = HeatmapAnalysisEngine()

def analyze_quiz_insights(quiz_id: int) -> List[Dict[str, Any]]:
    """
    Public function to analyze quiz and generate insights
    
    Args:
        quiz_id: ID of the quiz to analyze
        
    Returns:
        List of generated insights
    """
    return analysis_engine.analyze_quiz_performance(quiz_id)

def trigger_analysis_for_quiz(quiz_id: int) -> bool:
    """
    Trigger analysis for a quiz (can be called periodically or on-demand)
    
    Args:
        quiz_id: ID of the quiz to analyze
        
    Returns:
        True if analysis completed successfully
    """
    try:
        insights = analyze_quiz_insights(quiz_id)
        logging.info(f"Generated {len(insights)} insights for quiz {quiz_id}")
        return True
    except Exception as e:
        logging.error(f"Failed to analyze quiz {quiz_id}: {e}")
        return False