"""
BigBossizzz Enhanced Analytics & Insights Engine
Comprehensive analytics system with predictive capabilities, performance analysis, and pattern detection
"""

import json
import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import pandas as pd
from sqlalchemy import func, text, and_, or_
from sqlalchemy.orm import joinedload

from app import db
from models import (User, Quiz, Question, QuestionOption, QuizAttempt, Answer, 
                   ProctoringEvent, UserViolation, InteractionEvent, Course,
                   ParticipantEnrollment, SecurityAlert, CollaborationSignal,
                   AttemptSimilarity, PlagiarismAnalysis)

@dataclass
class StudentRiskProfile:
    """Student risk assessment profile"""
    user_id: int
    username: str
    risk_score: float
    risk_level: str
    risk_factors: List[str]
    intervention_recommendations: List[str]
    predicted_failure_probability: float
    engagement_score: float
    performance_trend: str
    last_activity: datetime
    courses_enrolled: int
    avg_quiz_score: float
    violation_count: int
    proctoring_issues: int

@dataclass
class QuestionAnalytics:
    """Question performance analytics"""
    question_id: int
    question_text: str
    difficulty_score: float
    difficulty_level: str
    discrimination_index: float
    average_score: float
    attempt_count: int
    correct_percentage: float
    time_to_complete_avg: float
    revision_needed: bool
    performance_category: str

@dataclass
class CheatingPattern:
    """Detected cheating pattern"""
    pattern_id: str
    pattern_type: str
    severity: str
    confidence_score: float
    participants: List[int]
    quiz_id: Optional[int]
    time_window: Tuple[datetime, datetime]
    evidence: Dict[str, Any]
    status: str
    detected_at: datetime

@dataclass
class InstitutionalMetrics:
    """Real-time institutional dashboard metrics"""
    total_students: int
    active_students_today: int
    quizzes_in_progress: int
    completed_quizzes_today: int
    average_performance: float
    high_risk_students: int
    security_alerts_today: int
    system_uptime: float
    concurrent_users: int
    violation_rate: float

class PredictiveAnalytics:
    """Advanced predictive analytics for student success"""
    
    def __init__(self):
        self.risk_model = None
        self.engagement_model = None
        self.performance_model = None
        self.feature_scaler = StandardScaler()
        self.model_accuracy = 0.0
        self.last_trained = None
        
    def analyze_student_risk(self, user_id: int = None, course_id: int = None) -> List[StudentRiskProfile]:
        """Analyze student risk profiles with predictive modeling"""
        
        try:
            # Get student data for analysis
            query = db.session.query(User).filter(User.role == 'participant')
            
            if user_id:
                query = query.filter(User.id == user_id)
            
            students = query.all()
            risk_profiles = []
            
            for student in students:
                profile = self._create_risk_profile(student, course_id)
                risk_profiles.append(profile)
            
            # Sort by risk score (highest first)
            risk_profiles.sort(key=lambda x: x.risk_score, reverse=True)
            
            return risk_profiles
            
        except Exception as e:
            logging.error(f"Error in student risk analysis: {e}")
            return []
    
    def _create_risk_profile(self, student: User, course_id: int = None) -> StudentRiskProfile:
        """Create comprehensive risk profile for a student"""
        
        # Get student's quiz attempts
        attempts_query = db.session.query(QuizAttempt).filter(
            QuizAttempt.participant_id == student.id
        )
        
        if course_id:
            attempts_query = attempts_query.join(Quiz).filter(Quiz.course_id == course_id)
        
        attempts = attempts_query.all()
        
        # Calculate engagement metrics
        engagement_score = self._calculate_engagement_score(student, attempts)
        
        # Calculate performance metrics
        performance_data = self._calculate_performance_metrics(student, attempts)
        
        # Get violation data
        violations = db.session.query(UserViolation).filter(
            UserViolation.user_id == student.id
        ).all()
        
        # Get proctoring events
        proctoring_events = db.session.query(ProctoringEvent).join(QuizAttempt).filter(
            QuizAttempt.participant_id == student.id
        ).all()
        
        # Calculate risk factors
        risk_factors = self._identify_risk_factors(student, attempts, violations, proctoring_events)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(
            engagement_score, performance_data, violations, proctoring_events, risk_factors
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate intervention recommendations
        recommendations = self._generate_interventions(risk_factors, risk_score, performance_data)
        
        # Predict failure probability
        failure_probability = self._predict_failure_probability(
            engagement_score, performance_data, risk_score
        )
        
        # Determine performance trend
        performance_trend = self._analyze_performance_trend(attempts)
        
        # Get enrollment data
        enrollments = db.session.query(ParticipantEnrollment).filter(
            ParticipantEnrollment.participant_id == student.id
        ).count()
        
        return StudentRiskProfile(
            user_id=student.id,
            username=student.username,
            risk_score=round(risk_score, 2),
            risk_level=risk_level,
            risk_factors=risk_factors,
            intervention_recommendations=recommendations,
            predicted_failure_probability=round(failure_probability, 3),
            engagement_score=round(engagement_score, 2),
            performance_trend=performance_trend,
            last_activity=self._get_last_activity(student),
            courses_enrolled=enrollments,
            avg_quiz_score=round(performance_data.get('avg_score', 0), 2),
            violation_count=len(violations),
            proctoring_issues=len([e for e in proctoring_events if e.severity in ['medium', 'high']])
        )
    
    def _calculate_engagement_score(self, student: User, attempts: List[QuizAttempt]) -> float:
        """Calculate student engagement score based on activity patterns"""
        
        if not attempts:
            return 0.0
        
        engagement_factors = {
            'quiz_completion_rate': 0.25,
            'time_management': 0.20,
            'consistency': 0.20,
            'effort_level': 0.15,
            'interaction_depth': 0.10,
            'help_seeking': 0.10
        }
        
        total_score = 0.0
        
        # Quiz completion rate
        completed = len([a for a in attempts if a.status == 'completed'])
        completion_rate = completed / len(attempts) if attempts else 0
        total_score += completion_rate * engagement_factors['quiz_completion_rate']
        
        # Time management (not rushing or taking too long)
        time_scores = []
        for attempt in attempts:
            if attempt.started_at and attempt.completed_at:
                duration = (attempt.completed_at - attempt.started_at).total_seconds() / 60
                quiz_time_limit = attempt.quiz.time_limit if attempt.quiz.time_limit else 60
                
                # Optimal time is 70-90% of allowed time
                optimal_min = quiz_time_limit * 0.7
                optimal_max = quiz_time_limit * 0.9
                
                if optimal_min <= duration <= optimal_max:
                    time_scores.append(1.0)
                elif duration < optimal_min:
                    time_scores.append(0.5)  # Rushing
                else:
                    time_scores.append(0.7)  # Taking time
        
        avg_time_score = statistics.mean(time_scores) if time_scores else 0.5
        total_score += avg_time_score * engagement_factors['time_management']
        
        # Consistency (regular quiz taking)
        if len(attempts) > 1:
            dates = [a.started_at.date() for a in attempts if a.started_at]
            if len(set(dates)) > 1:
                date_gaps = []
                sorted_dates = sorted(set(dates))
                for i in range(1, len(sorted_dates)):
                    gap = (sorted_dates[i] - sorted_dates[i-1]).days
                    date_gaps.append(gap)
                
                avg_gap = statistics.mean(date_gaps)
                consistency_score = max(0, 1 - (avg_gap / 14))  # Penalty for gaps > 2 weeks
                total_score += consistency_score * engagement_factors['consistency']
        
        # Effort level (based on answer changes and time spent)
        interaction_events = db.session.query(InteractionEvent).join(QuizAttempt).filter(
            QuizAttempt.participant_id == student.id
        ).all()
        
        effort_indicators = len([e for e in interaction_events if e.event_type == 'answer_change'])
        effort_score = min(1.0, effort_indicators / 10)  # Normalize to max 10 changes
        total_score += effort_score * engagement_factors['effort_level']
        
        # Interaction depth
        interaction_types = set([e.event_type for e in interaction_events])
        depth_score = len(interaction_types) / 6  # Normalize to 6 interaction types
        total_score += min(1.0, depth_score) * engagement_factors['interaction_depth']
        
        # Help seeking behavior (reasonable violation reports)
        help_seeking_score = 0.5  # Default neutral score
        total_score += help_seeking_score * engagement_factors['help_seeking']
        
        return min(100.0, total_score * 100)
    
    def _calculate_performance_metrics(self, student: User, attempts: List[QuizAttempt]) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        
        if not attempts:
            return {
                'avg_score': 0.0,
                'score_trend': 0.0,
                'consistency': 0.0,
                'improvement_rate': 0.0
            }
        
        scores = [a.score for a in attempts if a.score is not None]
        
        if not scores:
            return {
                'avg_score': 0.0,
                'score_trend': 0.0,
                'consistency': 0.0,
                'improvement_rate': 0.0
            }
        
        # Average score
        avg_score = statistics.mean(scores)
        
        # Score trend (using linear regression slope)
        if len(scores) > 1:
            x = list(range(len(scores)))
            slope = np.polyfit(x, scores, 1)[0]
            score_trend = slope
        else:
            score_trend = 0.0
        
        # Consistency (inverse of standard deviation)
        consistency = max(0, 100 - statistics.stdev(scores)) if len(scores) > 1 else 50
        
        # Improvement rate (comparing first half to second half)
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_half_avg = statistics.mean(scores[:mid])
            second_half_avg = statistics.mean(scores[mid:])
            improvement_rate = (second_half_avg - first_half_avg) / first_half_avg * 100
        else:
            improvement_rate = 0.0
        
        return {
            'avg_score': avg_score,
            'score_trend': score_trend,
            'consistency': consistency,
            'improvement_rate': improvement_rate
        }
    
    def _identify_risk_factors(self, student: User, attempts: List[QuizAttempt], 
                             violations: List[UserViolation], proctoring_events: List[ProctoringEvent]) -> List[str]:
        """Identify specific risk factors for the student"""
        
        risk_factors = []
        
        # Performance-based risk factors
        if attempts:
            scores = [a.score for a in attempts if a.score is not None]
            if scores:
                avg_score = statistics.mean(scores)
                if avg_score < 60:
                    risk_factors.append("Low average quiz scores")
                if len(scores) > 1 and scores[-1] < scores[0]:
                    risk_factors.append("Declining performance trend")
                
                # Check for sudden performance drops
                if len(scores) >= 3:
                    recent_avg = statistics.mean(scores[-3:])
                    overall_avg = statistics.mean(scores)
                    if recent_avg < overall_avg * 0.8:
                        risk_factors.append("Recent performance decline")
        
        # Engagement-based risk factors
        if len(attempts) < 3:
            risk_factors.append("Low quiz participation")
        
        incomplete_attempts = len([a for a in attempts if a.status != 'completed'])
        if incomplete_attempts > len(attempts) * 0.3:
            risk_factors.append("High incomplete attempt rate")
        
        # Check for irregular timing patterns
        if attempts:
            late_submissions = len([a for a in attempts if a.force_submitted])
            if late_submissions > len(attempts) * 0.2:
                risk_factors.append("Frequent time management issues")
        
        # Violation-based risk factors
        if violations:
            if len(violations) > 2:
                risk_factors.append("Multiple proctoring violations")
            
            flagged_violations = [v for v in violations if v.is_flagged]
            if flagged_violations:
                risk_factors.append("Flagged for suspicious behavior")
        
        # Proctoring event analysis
        high_severity_events = [e for e in proctoring_events if e.severity == 'high']
        if len(high_severity_events) > 5:
            risk_factors.append("Frequent high-severity proctoring alerts")
        
        # Activity patterns
        last_activity = self._get_last_activity(student)
        if last_activity and (datetime.utcnow() - last_activity).days > 14:
            risk_factors.append("Extended period of inactivity")
        
        return risk_factors
    
    def _calculate_risk_score(self, engagement_score: float, performance_data: Dict, 
                            violations: List, proctoring_events: List, risk_factors: List[str]) -> float:
        """Calculate overall risk score (0-100, higher = more risk)"""
        
        # Base risk from engagement (inverse relationship)
        engagement_risk = max(0, 100 - engagement_score)
        
        # Performance risk
        avg_score = performance_data.get('avg_score', 0)
        performance_risk = max(0, 100 - avg_score)
        
        # Trend risk
        score_trend = performance_data.get('score_trend', 0)
        trend_risk = max(0, -score_trend * 10)  # Negative trend increases risk
        
        # Violation risk
        violation_risk = min(50, len(violations) * 10)
        
        # Proctoring risk
        proctoring_risk = min(30, len(proctoring_events) * 2)
        
        # Risk factor penalty
        factor_risk = min(40, len(risk_factors) * 8)
        
        # Weighted combination
        total_risk = (
            engagement_risk * 0.25 +
            performance_risk * 0.30 +
            trend_risk * 0.15 +
            violation_risk * 0.15 +
            proctoring_risk * 0.10 +
            factor_risk * 0.05
        )
        
        return min(100.0, max(0.0, total_risk))
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level category"""
        if risk_score >= 80:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 40:
            return "Medium"
        elif risk_score >= 20:
            return "Low"
        else:
            return "Minimal"
    
    def _generate_interventions(self, risk_factors: List[str], risk_score: float, 
                              performance_data: Dict) -> List[str]:
        """Generate personalized intervention recommendations"""
        
        recommendations = []
        
        # Performance-based interventions
        if "Low average quiz scores" in risk_factors:
            recommendations.append("Schedule one-on-one tutoring sessions")
            recommendations.append("Provide additional practice materials")
        
        if "Declining performance trend" in risk_factors:
            recommendations.append("Immediate academic counseling session")
            recommendations.append("Review study strategies and time management")
        
        # Engagement interventions
        if "Low quiz participation" in risk_factors:
            recommendations.append("Send engagement reminders and check-ins")
            recommendations.append("Investigate potential technical or personal barriers")
        
        if "High incomplete attempt rate" in risk_factors:
            recommendations.append("Time management workshop enrollment")
            recommendations.append("Extend quiz time limits or provide breaks")
        
        # Behavioral interventions
        if "Multiple proctoring violations" in risk_factors:
            recommendations.append("Academic integrity training required")
            recommendations.append("Supervised testing environment")
        
        if "Extended period of inactivity" in risk_factors:
            recommendations.append("Immediate outreach contact")
            recommendations.append("Check for withdrawal or personal issues")
        
        # Risk level specific interventions
        if risk_score >= 80:
            recommendations.append("Emergency academic intervention meeting")
            recommendations.append("Consider course withdrawal/incomplete options")
        elif risk_score >= 60:
            recommendations.append("Weekly check-ins with instructor")
            recommendations.append("Peer study group assignment")
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(recommendations))
    
    def _predict_failure_probability(self, engagement_score: float, performance_data: Dict, risk_score: float) -> float:
        """Predict probability of course failure using multiple factors"""
        
        # Simple logistic regression-like calculation
        avg_score = performance_data.get('avg_score', 0)
        score_trend = performance_data.get('score_trend', 0)
        
        # Feature weights based on education research
        weights = {
            'performance': 0.4,
            'engagement': 0.25,
            'trend': 0.20,
            'risk': 0.15
        }
        
        # Normalize factors to 0-1 scale for probability calculation
        performance_factor = max(0, min(1, (100 - avg_score) / 100))
        engagement_factor = max(0, min(1, (100 - engagement_score) / 100))
        trend_factor = max(0, min(1, max(0, -score_trend) / 10))
        risk_factor = max(0, min(1, risk_score / 100))
        
        # Calculate weighted probability
        failure_probability = (
            performance_factor * weights['performance'] +
            engagement_factor * weights['engagement'] +
            trend_factor * weights['trend'] +
            risk_factor * weights['risk']
        )
        
        return min(0.99, max(0.01, failure_probability))
    
    def _analyze_performance_trend(self, attempts: List[QuizAttempt]) -> str:
        """Analyze overall performance trend"""
        
        if len(attempts) < 3:
            return "Insufficient Data"
        
        scores = [a.score for a in attempts if a.score is not None]
        
        if len(scores) < 3:
            return "Insufficient Data"
        
        # Calculate trend using linear regression
        x = list(range(len(scores)))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 2:
            return "Strongly Improving"
        elif slope > 0.5:
            return "Improving"
        elif slope > -0.5:
            return "Stable"
        elif slope > -2:
            return "Declining"
        else:
            return "Strongly Declining"
    
    def _get_last_activity(self, student: User) -> Optional[datetime]:
        """Get student's last activity timestamp"""
        
        # Check quiz attempts
        last_attempt = db.session.query(QuizAttempt).filter(
            QuizAttempt.participant_id == student.id
        ).order_by(QuizAttempt.started_at.desc()).first()
        
        # Check interaction events
        last_interaction = db.session.query(InteractionEvent).join(QuizAttempt).filter(
            QuizAttempt.participant_id == student.id
        ).order_by(InteractionEvent.timestamp.desc()).first()
        
        activities = []
        if last_attempt and last_attempt.started_at:
            activities.append(last_attempt.started_at)
        if last_interaction and last_interaction.timestamp:
            activities.append(last_interaction.timestamp)
        
        return max(activities) if activities else None

class QuestionPerformanceAnalyzer:
    """Analyze question difficulty and effectiveness"""
    
    def analyze_question_performance(self, question_id: int = None, quiz_id: int = None) -> List[QuestionAnalytics]:
        """Comprehensive question performance analysis"""
        
        try:
            query = db.session.query(Question)
            
            if question_id:
                query = query.filter(Question.id == question_id)
            elif quiz_id:
                query = query.filter(Question.quiz_id == quiz_id)
            
            questions = query.all()
            analytics_results = []
            
            for question in questions:
                analytics = self._analyze_single_question(question)
                analytics_results.append(analytics)
            
            return analytics_results
            
        except Exception as e:
            logging.error(f"Error in question performance analysis: {e}")
            return []
    
    def _analyze_single_question(self, question: Question) -> QuestionAnalytics:
        """Analyze performance of a single question"""
        
        # Get all answers for this question
        answers = db.session.query(Answer).filter(Answer.question_id == question.id).all()
        
        if not answers:
            return QuestionAnalytics(
                question_id=question.id,
                question_text=question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text,
                difficulty_score=50.0,
                difficulty_level="Unknown",
                discrimination_index=0.0,
                average_score=0.0,
                attempt_count=0,
                correct_percentage=0.0,
                time_to_complete_avg=0.0,
                revision_needed=False,
                performance_category="No Data"
            )
        
        # Calculate basic statistics
        attempt_count = len(answers)
        correct_answers = len([a for a in answers if a.is_correct])
        correct_percentage = (correct_answers / attempt_count) * 100 if attempt_count > 0 else 0
        
        # Calculate average score
        scores = [a.points_earned for a in answers if a.points_earned is not None]
        average_score = statistics.mean(scores) if scores else 0
        
        # Calculate difficulty score (inverse of correct percentage)
        difficulty_score = 100 - correct_percentage
        
        # Determine difficulty level
        difficulty_level = self._categorize_difficulty(difficulty_score)
        
        # Calculate discrimination index (how well question differentiates high/low performers)
        discrimination_index = self._calculate_discrimination_index(question, answers)
        
        # Calculate average time to complete
        time_to_complete_avg = self._calculate_average_completion_time(answers)
        
        # Determine if revision is needed
        revision_needed = self._needs_revision(difficulty_score, discrimination_index, correct_percentage)
        
        # Categorize performance
        performance_category = self._categorize_performance(difficulty_score, discrimination_index, correct_percentage)
        
        return QuestionAnalytics(
            question_id=question.id,
            question_text=question.question_text[:100] + "..." if len(question.question_text) > 100 else question.question_text,
            difficulty_score=round(difficulty_score, 2),
            difficulty_level=difficulty_level,
            discrimination_index=round(discrimination_index, 3),
            average_score=round(average_score, 2),
            attempt_count=attempt_count,
            correct_percentage=round(correct_percentage, 2),
            time_to_complete_avg=round(time_to_complete_avg, 2),
            revision_needed=revision_needed,
            performance_category=performance_category
        )
    
    def _categorize_difficulty(self, difficulty_score: float) -> str:
        """Categorize question difficulty level"""
        if difficulty_score >= 80:
            return "Very Hard"
        elif difficulty_score >= 60:
            return "Hard"
        elif difficulty_score >= 40:
            return "Moderate"
        elif difficulty_score >= 20:
            return "Easy"
        else:
            return "Very Easy"
    
    def _calculate_discrimination_index(self, question: Question, answers: List[Answer]) -> float:
        """Calculate discrimination index using upper/lower group method"""
        
        if len(answers) < 10:
            return 0.0
        
        # Get quiz attempt scores for context
        attempt_scores = {}
        for answer in answers:
            attempt = db.session.query(QuizAttempt).filter(
                QuizAttempt.id == answer.attempt_id
            ).first()
            if attempt and attempt.score is not None:
                attempt_scores[answer.id] = attempt.score
        
        if len(attempt_scores) < 10:
            return 0.0
        
        # Sort answers by overall quiz performance
        sorted_answers = sorted(answers, key=lambda a: attempt_scores.get(a.id, 0), reverse=True)
        
        # Get upper and lower 27% groups (standard practice)
        group_size = max(1, int(len(sorted_answers) * 0.27))
        upper_group = sorted_answers[:group_size]
        lower_group = sorted_answers[-group_size:]
        
        # Calculate correct percentages for each group
        upper_correct = len([a for a in upper_group if a.is_correct]) / len(upper_group)
        lower_correct = len([a for a in lower_group if a.is_correct]) / len(lower_group)
        
        # Discrimination index = P_upper - P_lower
        return upper_correct - lower_correct
    
    def _calculate_average_completion_time(self, answers: List[Answer]) -> float:
        """Calculate average time to complete question"""
        
        completion_times = []
        
        for answer in answers:
            # Get interaction events for this answer
            interactions = db.session.query(InteractionEvent).filter(
                InteractionEvent.question_id == answer.question_id,
                InteractionEvent.attempt_id == answer.attempt_id
            ).order_by(InteractionEvent.timestamp).all()
            
            if len(interactions) >= 2:
                start_time = interactions[0].timestamp
                end_time = interactions[-1].timestamp
                duration = (end_time - start_time).total_seconds()
                completion_times.append(duration)
        
        return statistics.mean(completion_times) if completion_times else 0.0
    
    def _needs_revision(self, difficulty_score: float, discrimination_index: float, correct_percentage: float) -> bool:
        """Determine if question needs revision"""
        
        # Question needs revision if:
        # 1. Too easy (>90% correct) or too hard (<10% correct)
        # 2. Poor discrimination (< 0.2)
        # 3. Very low or negative discrimination
        
        if correct_percentage > 90 or correct_percentage < 10:
            return True
        
        if discrimination_index < 0.2:
            return True
        
        if discrimination_index < 0:
            return True
        
        return False
    
    def _categorize_performance(self, difficulty_score: float, discrimination_index: float, correct_percentage: float) -> str:
        """Categorize overall question performance"""
        
        if discrimination_index >= 0.4 and 20 <= correct_percentage <= 80:
            return "Excellent"
        elif discrimination_index >= 0.3 and 15 <= correct_percentage <= 85:
            return "Good"
        elif discrimination_index >= 0.2 and 10 <= correct_percentage <= 90:
            return "Acceptable"
        elif discrimination_index >= 0.1:
            return "Needs Improvement"
        else:
            return "Poor"

class CheatingPatternDetector:
    """Advanced cheating pattern detection and analysis"""
    
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.clustering_model = DBSCAN(eps=0.5, min_samples=3)
        
    def detect_cheating_patterns(self, quiz_id: int = None, time_window_hours: int = 24) -> List[CheatingPattern]:
        """Detect various cheating patterns across quizzes"""
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window_hours)
            
            patterns = []
            
            # Detect different types of cheating patterns
            patterns.extend(self._detect_answer_similarity_patterns(quiz_id, start_time, end_time))
            patterns.extend(self._detect_timing_patterns(quiz_id, start_time, end_time))
            patterns.extend(self._detect_ip_clustering_patterns(quiz_id, start_time, end_time))
            patterns.extend(self._detect_behavioral_anomalies(quiz_id, start_time, end_time))
            patterns.extend(self._detect_collaboration_signals(quiz_id, start_time, end_time))
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error in cheating pattern detection: {e}")
            return []
    
    def _detect_answer_similarity_patterns(self, quiz_id: int, start_time: datetime, end_time: datetime) -> List[CheatingPattern]:
        """Detect unusual answer similarity patterns"""
        
        patterns = []
        
        # Get quiz attempts in time window
        query = db.session.query(QuizAttempt).filter(
            QuizAttempt.started_at >= start_time,
            QuizAttempt.started_at <= end_time
        )
        
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == quiz_id)
        
        attempts = query.all()
        
        if len(attempts) < 2:
            return patterns
        
        # Check for highly similar answer patterns
        similarity_matrix = {}
        
        for i, attempt1 in enumerate(attempts):
            for j, attempt2 in enumerate(attempts[i+1:], i+1):
                similarity_score = self._calculate_answer_similarity(attempt1, attempt2)
                
                if similarity_score > 0.8:  # High similarity threshold
                    pattern_id = f"answer_similarity_{attempt1.id}_{attempt2.id}_{int(datetime.utcnow().timestamp())}"
                    
                    pattern = CheatingPattern(
                        pattern_id=pattern_id,
                        pattern_type="Answer Similarity",
                        severity="High" if similarity_score > 0.9 else "Medium",
                        confidence_score=similarity_score,
                        participants=[attempt1.participant_id, attempt2.participant_id],
                        quiz_id=attempt1.quiz_id,
                        time_window=(min(attempt1.started_at, attempt2.started_at), 
                                   max(attempt1.completed_at or attempt1.started_at, 
                                       attempt2.completed_at or attempt2.started_at)),
                        evidence={
                            "similarity_score": similarity_score,
                            "matching_answers": self._get_matching_answers(attempt1, attempt2),
                            "attempt_ids": [attempt1.id, attempt2.id]
                        },
                        status="Active",
                        detected_at=datetime.utcnow()
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_timing_patterns(self, quiz_id: int, start_time: datetime, end_time: datetime) -> List[CheatingPattern]:
        """Detect suspicious timing patterns"""
        
        patterns = []
        
        # Get attempts with completion times
        query = db.session.query(QuizAttempt).filter(
            QuizAttempt.started_at >= start_time,
            QuizAttempt.started_at <= end_time,
            QuizAttempt.completed_at.isnot(None)
        )
        
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == quiz_id)
        
        attempts = query.all()
        
        if len(attempts) < 3:
            return patterns
        
        # Group by quiz and analyze timing
        quiz_groups = defaultdict(list)
        for attempt in attempts:
            quiz_groups[attempt.quiz_id].append(attempt)
        
        for quiz_id, quiz_attempts in quiz_groups.items():
            if len(quiz_attempts) < 3:
                continue
            
            # Calculate completion times
            completion_times = []
            for attempt in quiz_attempts:
                duration = (attempt.completed_at - attempt.started_at).total_seconds() / 60
                completion_times.append((attempt, duration))
            
            # Detect unusually fast completions
            durations = [ct[1] for ct in completion_times]
            if len(durations) > 2:
                mean_duration = statistics.mean(durations)
                std_duration = statistics.stdev(durations) if len(durations) > 1 else 0
                
                for attempt, duration in completion_times:
                    if duration < mean_duration - 2 * std_duration and duration < mean_duration * 0.5:
                        pattern_id = f"fast_completion_{attempt.id}_{int(datetime.utcnow().timestamp())}"
                        
                        pattern = CheatingPattern(
                            pattern_id=pattern_id,
                            pattern_type="Suspicious Timing",
                            severity="Medium",
                            confidence_score=min(0.9, (mean_duration - duration) / mean_duration),
                            participants=[attempt.participant_id],
                            quiz_id=quiz_id,
                            time_window=(attempt.started_at, attempt.completed_at),
                            evidence={
                                "completion_time_minutes": duration,
                                "average_time_minutes": mean_duration,
                                "deviation_factor": (mean_duration - duration) / mean_duration
                            },
                            status="Active",
                            detected_at=datetime.utcnow()
                        )
                        
                        patterns.append(pattern)
        
        return patterns
    
    def _detect_ip_clustering_patterns(self, quiz_id: int, start_time: datetime, end_time: datetime) -> List[CheatingPattern]:
        """Detect IP address clustering that might indicate collusion"""
        
        patterns = []
        
        # Get attempts with IP addresses from proctoring events
        query = db.session.query(QuizAttempt).join(ProctoringEvent).filter(
            QuizAttempt.started_at >= start_time,
            QuizAttempt.started_at <= end_time,
            ProctoringEvent.ip_address.isnot(None)
        )
        
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == quiz_id)
        
        attempts = query.all()
        
        # Group by IP address
        ip_groups = defaultdict(list)
        for attempt in attempts:
            # Get IP from proctoring events
            proctoring_event = db.session.query(ProctoringEvent).filter(
                ProctoringEvent.attempt_id == attempt.id,
                ProctoringEvent.ip_address.isnot(None)
            ).first()
            
            if proctoring_event and proctoring_event.ip_address:
                ip_groups[proctoring_event.ip_address].append(attempt)
        
        # Check for suspicious IP clustering
        for ip_address, ip_attempts in ip_groups.items():
            if len(ip_attempts) > 2:  # More than 2 attempts from same IP
                # Check if they're different users
                user_ids = set(attempt.participant_id for attempt in ip_attempts)
                
                if len(user_ids) > 1:  # Multiple users from same IP
                    pattern_id = f"ip_clustering_{ip_address.replace('.', '_')}_{int(datetime.utcnow().timestamp())}"
                    
                    pattern = CheatingPattern(
                        pattern_id=pattern_id,
                        pattern_type="IP Clustering",
                        severity="Medium",
                        confidence_score=min(0.8, len(user_ids) / 5),  # Higher score for more users
                        participants=list(user_ids),
                        quiz_id=ip_attempts[0].quiz_id,
                        time_window=(min(a.started_at for a in ip_attempts),
                                   max(a.completed_at or a.started_at for a in ip_attempts)),
                        evidence={
                            "ip_address": ip_address,
                            "user_count": len(user_ids),
                            "attempt_count": len(ip_attempts),
                            "attempt_ids": [a.id for a in ip_attempts]
                        },
                        status="Active",
                        detected_at=datetime.utcnow()
                    )
                    
                    patterns.append(pattern)
        
        return patterns
    
    def _detect_behavioral_anomalies(self, quiz_id: int, start_time: datetime, end_time: datetime) -> List[CheatingPattern]:
        """Detect behavioral anomalies using machine learning"""
        
        patterns = []
        
        try:
            # Get interaction events for analysis
            query = db.session.query(InteractionEvent).join(QuizAttempt).filter(
                QuizAttempt.started_at >= start_time,
                QuizAttempt.started_at <= end_time
            )
            
            if quiz_id:
                query = query.filter(QuizAttempt.quiz_id == quiz_id)
            
            interactions = query.all()
            
            if len(interactions) < 50:  # Need sufficient data for anomaly detection
                return patterns
            
            # Create feature vectors for anomaly detection
            features = []
            attempt_mapping = {}
            
            # Group interactions by attempt
            attempt_interactions = defaultdict(list)
            for interaction in interactions:
                attempt_interactions[interaction.attempt_id].append(interaction)
            
            for attempt_id, attempt_events in attempt_interactions.items():
                if len(attempt_events) < 5:  # Skip attempts with too few interactions
                    continue
                
                feature_vector = self._extract_behavioral_features(attempt_events)
                features.append(feature_vector)
                attempt_mapping[len(features) - 1] = attempt_id
            
            if len(features) < 10:
                return patterns
            
            # Detect anomalies
            feature_array = np.array(features)
            anomaly_scores = self.anomaly_detector.fit_predict(feature_array)
            
            # Identify anomalous attempts
            for idx, score in enumerate(anomaly_scores):
                if score == -1:  # Anomaly detected
                    attempt_id = attempt_mapping[idx]
                    attempt = db.session.query(QuizAttempt).get(attempt_id)
                    
                    if attempt:
                        pattern_id = f"behavioral_anomaly_{attempt_id}_{int(datetime.utcnow().timestamp())}"
                        
                        pattern = CheatingPattern(
                            pattern_id=pattern_id,
                            pattern_type="Behavioral Anomaly",
                            severity="Medium",
                            confidence_score=0.7,
                            participants=[attempt.participant_id],
                            quiz_id=attempt.quiz_id,
                            time_window=(attempt.started_at, attempt.completed_at or attempt.started_at),
                            evidence={
                                "anomaly_score": float(score),
                                "feature_vector": features[idx],
                                "unusual_patterns": self._describe_anomaly(features[idx])
                            },
                            status="Active",
                            detected_at=datetime.utcnow()
                        )
                        
                        patterns.append(pattern)
        
        except Exception as e:
            logging.error(f"Error in behavioral anomaly detection: {e}")
        
        return patterns
    
    def _detect_collaboration_signals(self, quiz_id: int, start_time: datetime, end_time: datetime) -> List[CheatingPattern]:
        """Detect collaboration signals from existing collaboration analysis"""
        
        patterns = []
        
        # Get collaboration signals from the database
        query = db.session.query(CollaborationSignal).filter(
            CollaborationSignal.created_at >= start_time,
            CollaborationSignal.created_at <= end_time,
            CollaborationSignal.severity.in_(['warn', 'high'])
        )
        
        if quiz_id:
            query = query.filter(CollaborationSignal.quiz_id == quiz_id)
        
        signals = query.all()
        
        for signal in signals:
            pattern_id = f"collaboration_{signal.id}_{int(datetime.utcnow().timestamp())}"
            
            pattern = CheatingPattern(
                pattern_id=pattern_id,
                pattern_type="Collaboration Detected",
                severity="High" if signal.severity == 'high' else "Medium",
                confidence_score=signal.score,
                participants=signal.participants if signal.participants else [],
                quiz_id=signal.quiz_id,
                time_window=(signal.window_start, signal.window_end),
                evidence={
                    "signal_type": signal.signal_type,
                    "signal_details": signal.details,
                    "collaboration_score": signal.score
                },
                status="Active",
                detected_at=signal.created_at
            )
            
            patterns.append(pattern)
        
        return patterns
    
    def _calculate_answer_similarity(self, attempt1: QuizAttempt, attempt2: QuizAttempt) -> float:
        """Calculate similarity score between two quiz attempts"""
        
        # Get answers for both attempts
        answers1 = db.session.query(Answer).filter(Answer.attempt_id == attempt1.id).all()
        answers2 = db.session.query(Answer).filter(Answer.attempt_id == attempt2.id).all()
        
        if not answers1 or not answers2:
            return 0.0
        
        # Create answer mappings by question
        answer_map1 = {a.question_id: a for a in answers1}
        answer_map2 = {a.question_id: a for a in answers2}
        
        # Compare answers for common questions
        common_questions = set(answer_map1.keys()) & set(answer_map2.keys())
        
        if not common_questions:
            return 0.0
        
        matches = 0
        total = len(common_questions)
        
        for question_id in common_questions:
            ans1 = answer_map1[question_id]
            ans2 = answer_map2[question_id]
            
            # Compare answer content
            if ans1.selected_option_id and ans2.selected_option_id:
                if ans1.selected_option_id == ans2.selected_option_id:
                    matches += 1
            elif ans1.answer_text and ans2.answer_text:
                # For text answers, use similarity threshold
                similarity = self._text_similarity(ans1.answer_text, ans2.answer_text)
                if similarity > 0.8:
                    matches += 1
        
        return matches / total if total > 0 else 0.0
    
    def _get_matching_answers(self, attempt1: QuizAttempt, attempt2: QuizAttempt) -> List[Dict]:
        """Get detailed information about matching answers"""
        
        answers1 = db.session.query(Answer).filter(Answer.attempt_id == attempt1.id).all()
        answers2 = db.session.query(Answer).filter(Answer.attempt_id == attempt2.id).all()
        
        answer_map1 = {a.question_id: a for a in answers1}
        answer_map2 = {a.question_id: a for a in answers2}
        
        matches = []
        common_questions = set(answer_map1.keys()) & set(answer_map2.keys())
        
        for question_id in common_questions:
            ans1 = answer_map1[question_id]
            ans2 = answer_map2[question_id]
            
            is_match = False
            match_type = "No Match"
            
            if ans1.selected_option_id and ans2.selected_option_id:
                if ans1.selected_option_id == ans2.selected_option_id:
                    is_match = True
                    match_type = "Identical Option"
            elif ans1.answer_text and ans2.answer_text:
                similarity = self._text_similarity(ans1.answer_text, ans2.answer_text)
                if similarity > 0.8:
                    is_match = True
                    match_type = f"Text Similarity ({similarity:.2f})"
            
            if is_match:
                matches.append({
                    "question_id": question_id,
                    "match_type": match_type,
                    "answer1": ans1.selected_option_id or ans1.answer_text,
                    "answer2": ans2.selected_option_id or ans2.answer_text
                })
        
        return matches
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap"""
        
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_behavioral_features(self, interactions: List[InteractionEvent]) -> List[float]:
        """Extract behavioral features from interaction events"""
        
        features = []
        
        # Time-based features
        timestamps = [i.timestamp for i in interactions]
        time_gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            time_gaps.append(gap)
        
        features.extend([
            len(interactions),  # Total interactions
            statistics.mean(time_gaps) if time_gaps else 0,  # Average time between interactions
            statistics.stdev(time_gaps) if len(time_gaps) > 1 else 0,  # Time gap variance
            max(time_gaps) if time_gaps else 0,  # Maximum gap
            min(time_gaps) if time_gaps else 0,  # Minimum gap
        ])
        
        # Interaction type distribution
        interaction_types = [i.event_type for i in interactions]
        type_counts = Counter(interaction_types)
        
        # Normalize to percentages
        total_interactions = len(interactions)
        features.extend([
            type_counts.get('click', 0) / total_interactions,
            type_counts.get('focus', 0) / total_interactions,
            type_counts.get('scroll', 0) / total_interactions,
            type_counts.get('answer_change', 0) / total_interactions,
            len(set(interaction_types)) / 6,  # Diversity of interaction types
        ])
        
        # Position-based features
        positions = [(i.x_coordinate, i.y_coordinate) for i in interactions if i.x_coordinate and i.y_coordinate]
        if positions:
            x_coords = [p[0] for p in positions]
            y_coords = [p[1] for p in positions]
            
            features.extend([
                statistics.stdev(x_coords) if len(x_coords) > 1 else 0,
                statistics.stdev(y_coords) if len(y_coords) > 1 else 0,
                max(x_coords) - min(x_coords) if x_coords else 0,
                max(y_coords) - min(y_coords) if y_coords else 0,
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        return features
    
    def _describe_anomaly(self, feature_vector: List[float]) -> List[str]:
        """Describe what makes this behavioral pattern anomalous"""
        
        descriptions = []
        
        # Analyze specific features
        if feature_vector[0] < 5:  # Very few interactions
            descriptions.append("Unusually low interaction count")
        elif feature_vector[0] > 100:  # Too many interactions
            descriptions.append("Unusually high interaction count")
        
        if feature_vector[1] > 60:  # Long gaps between interactions
            descriptions.append("Extended periods of inactivity")
        elif feature_vector[1] < 1:  # Very rapid interactions
            descriptions.append("Abnormally rapid interaction patterns")
        
        if feature_vector[9] < 0.1:  # Low interaction diversity
            descriptions.append("Limited interaction pattern diversity")
        
        if not descriptions:
            descriptions.append("Unusual behavioral pattern detected")
        
        return descriptions

class InstitutionalDashboard:
    """Real-time institutional dashboard and monitoring"""
    
    def get_real_time_metrics(self) -> InstitutionalMetrics:
        """Get comprehensive real-time institutional metrics"""
        
        try:
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            # Total students
            total_students = db.session.query(User).filter(User.role == 'participant').count()
            
            # Active students today (had any activity)
            active_students_today = db.session.query(User).filter(
                User.role == 'participant',
                User.id.in_(
                    db.session.query(QuizAttempt.participant_id).filter(
                        QuizAttempt.started_at >= today_start
                    )
                )
            ).count()
            
            # Quizzes in progress
            quizzes_in_progress = db.session.query(QuizAttempt).filter(
                QuizAttempt.status == 'in_progress'
            ).count()
            
            # Completed quizzes today
            completed_quizzes_today = db.session.query(QuizAttempt).filter(
                QuizAttempt.completed_at >= today_start,
                QuizAttempt.status == 'completed'
            ).count()
            
            # Average performance today
            today_scores = db.session.query(QuizAttempt.score).filter(
                QuizAttempt.completed_at >= today_start,
                QuizAttempt.score.isnot(None)
            ).all()
            
            average_performance = statistics.mean([s[0] for s in today_scores]) if today_scores else 0.0
            
            # High risk students (using predictive analytics)
            predictor = PredictiveAnalytics()
            risk_profiles = predictor.analyze_student_risk()
            high_risk_students = len([p for p in risk_profiles if p.risk_level in ['High', 'Critical']])
            
            # Security alerts today
            security_alerts_today = db.session.query(SecurityAlert).filter(
                SecurityAlert.created_at >= today_start
            ).count()
            
            # System uptime (simplified - would be more complex in production)
            system_uptime = 99.5  # Placeholder
            
            # Concurrent users (simplified - would use real session tracking)
            concurrent_users = db.session.query(QuizAttempt).filter(
                QuizAttempt.status == 'in_progress'
            ).count()
            
            # Violation rate
            total_attempts_today = db.session.query(QuizAttempt).filter(
                QuizAttempt.started_at >= today_start
            ).count()
            
            violated_attempts = db.session.query(QuizAttempt).filter(
                QuizAttempt.started_at >= today_start,
                QuizAttempt.is_flagged == True
            ).count()
            
            violation_rate = (violated_attempts / total_attempts_today * 100) if total_attempts_today > 0 else 0
            
            return InstitutionalMetrics(
                total_students=total_students,
                active_students_today=active_students_today,
                quizzes_in_progress=quizzes_in_progress,
                completed_quizzes_today=completed_quizzes_today,
                average_performance=round(average_performance, 2),
                high_risk_students=high_risk_students,
                security_alerts_today=security_alerts_today,
                system_uptime=system_uptime,
                concurrent_users=concurrent_users,
                violation_rate=round(violation_rate, 2)
            )
            
        except Exception as e:
            logging.error(f"Error generating institutional metrics: {e}")
            return InstitutionalMetrics(
                total_students=0, active_students_today=0, quizzes_in_progress=0,
                completed_quizzes_today=0, average_performance=0.0, high_risk_students=0,
                security_alerts_today=0, system_uptime=0.0, concurrent_users=0, violation_rate=0.0
            )
    
    def get_live_monitoring_data(self) -> Dict[str, Any]:
        """Get live monitoring data for real-time dashboard updates"""
        
        try:
            # Current active sessions
            active_sessions = db.session.query(QuizAttempt).filter(
                QuizAttempt.status == 'in_progress'
            ).options(joinedload(QuizAttempt.participant), joinedload(QuizAttempt.quiz)).all()
            
            # Recent alerts (last hour)
            recent_alerts = db.session.query(SecurityAlert).filter(
                SecurityAlert.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).order_by(SecurityAlert.created_at.desc()).limit(10).all()
            
            # Performance trends (last 24 hours)
            performance_data = self._get_performance_trends()
            
            # System health metrics
            system_health = self._get_system_health()
            
            return {
                'active_sessions': [
                    {
                        'attempt_id': session.id,
                        'participant': session.participant.username,
                        'quiz': session.quiz.title,
                        'started_at': session.started_at.isoformat(),
                        'duration_minutes': (datetime.utcnow() - session.started_at).total_seconds() / 60
                    }
                    for session in active_sessions
                ],
                'recent_alerts': [
                    {
                        'id': alert.id,
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'user_id': alert.user_id,
                        'description': alert.description,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in recent_alerts
                ],
                'performance_trends': performance_data,
                'system_health': system_health,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error generating live monitoring data: {e}")
            return {
                'active_sessions': [],
                'recent_alerts': [],
                'performance_trends': {},
                'system_health': {},
                'last_updated': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trend data for the last 24 hours"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Hourly completion counts
        hourly_completions = db.session.query(
            func.date_trunc('hour', QuizAttempt.completed_at).label('hour'),
            func.count(QuizAttempt.id).label('count'),
            func.avg(QuizAttempt.score).label('avg_score')
        ).filter(
            QuizAttempt.completed_at >= start_time,
            QuizAttempt.completed_at <= end_time,
            QuizAttempt.status == 'completed'
        ).group_by('hour').order_by('hour').all()
        
        return {
            'hourly_data': [
                {
                    'hour': row.hour.isoformat(),
                    'completions': row.count,
                    'average_score': round(float(row.avg_score), 2) if row.avg_score else 0
                }
                for row in hourly_completions
            ]
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        
        # Database connection health
        try:
            db.session.execute(text('SELECT 1'))
            db_health = 'healthy'
        except Exception:
            db_health = 'unhealthy'
        
        # Recent error rates
        recent_errors = db.session.query(SecurityAlert).filter(
            SecurityAlert.created_at >= datetime.utcnow() - timedelta(hours=1),
            SecurityAlert.severity == 'critical'
        ).count()
        
        return {
            'database_status': db_health,
            'critical_errors_last_hour': recent_errors,
            'system_load': 'normal',  # Placeholder - would integrate with system monitoring
            'memory_usage': 75.5,  # Placeholder
            'disk_usage': 45.2,  # Placeholder
            'last_checked': datetime.utcnow().isoformat()
        }

# Main Analytics Engine
class AnalyticsEngine:
    """Main analytics engine coordinating all analysis modules"""
    
    def __init__(self):
        self.predictive_analytics = PredictiveAnalytics()
        self.question_analyzer = QuestionPerformanceAnalyzer()
        self.cheating_detector = CheatingPatternDetector()
        self.dashboard = InstitutionalDashboard()
    
    def generate_comprehensive_report(self, scope: str = 'institutional') -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        
        try:
            report = {
                'report_id': f'analytics_report_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}',
                'generated_at': datetime.utcnow().isoformat(),
                'scope': scope,
                'predictive_analytics': {},
                'question_performance': {},
                'cheating_patterns': {},
                'institutional_metrics': {}
            }
            
            # Student risk analysis
            risk_profiles = self.predictive_analytics.analyze_student_risk()
            report['predictive_analytics'] = {
                'total_students_analyzed': len(risk_profiles),
                'high_risk_students': len([p for p in risk_profiles if p.risk_level in ['High', 'Critical']]),
                'risk_distribution': Counter(p.risk_level for p in risk_profiles),
                'top_risk_factors': self._get_top_risk_factors(risk_profiles),
                'intervention_recommendations': self._get_intervention_summary(risk_profiles)
            }
            
            # Question performance analysis
            question_analytics = self.question_analyzer.analyze_question_performance()
            report['question_performance'] = {
                'questions_analyzed': len(question_analytics),
                'questions_needing_revision': len([q for q in question_analytics if q.revision_needed]),
                'difficulty_distribution': Counter(q.difficulty_level for q in question_analytics),
                'performance_categories': Counter(q.performance_category for q in question_analytics),
                'average_discrimination_index': statistics.mean([q.discrimination_index for q in question_analytics]) if question_analytics else 0
            }
            
            # Cheating pattern detection
            cheating_patterns = self.cheating_detector.detect_cheating_patterns()
            report['cheating_patterns'] = {
                'patterns_detected': len(cheating_patterns),
                'pattern_types': Counter(p.pattern_type for p in cheating_patterns),
                'severity_distribution': Counter(p.severity for p in cheating_patterns),
                'students_involved': len(set(user_id for p in cheating_patterns for user_id in p.participants))
            }
            
            # Institutional metrics
            institutional_metrics = self.dashboard.get_real_time_metrics()
            report['institutional_metrics'] = {
                'total_students': institutional_metrics.total_students,
                'active_students_today': institutional_metrics.active_students_today,
                'average_performance': institutional_metrics.average_performance,
                'violation_rate': institutional_metrics.violation_rate,
                'system_uptime': institutional_metrics.system_uptime
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating comprehensive analytics report: {e}")
            return {'error': str(e)}
    
    def _get_top_risk_factors(self, risk_profiles: List[StudentRiskProfile]) -> List[Tuple[str, int]]:
        """Get most common risk factors across all students"""
        
        all_factors = []
        for profile in risk_profiles:
            all_factors.extend(profile.risk_factors)
        
        factor_counts = Counter(all_factors)
        return factor_counts.most_common(10)
    
    def _get_intervention_summary(self, risk_profiles: List[StudentRiskProfile]) -> Dict[str, int]:
        """Summarize intervention recommendations"""
        
        all_interventions = []
        for profile in risk_profiles:
            all_interventions.extend(profile.intervention_recommendations)
        
        intervention_counts = Counter(all_interventions)
        return dict(intervention_counts.most_common(10))

# Factory function for easy access
def get_analytics_engine():
    """Get initialized analytics engine instance"""
    return AnalyticsEngine()