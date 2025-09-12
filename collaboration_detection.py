"""
Real-time collaboration detection service for quiz proctoring.
Detects suspicious patterns indicating possible collaboration between participants.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import math

from app import db, redis_client, socketio
from models import (
    CollaborationSignal, AttemptSimilarity, QuizAttempt, 
    Answer, User, DeviceLog, SecurityAlert
)


class CollaborationDetector:
    """Main collaboration detection engine."""
    
    def __init__(self):
        self.answer_cache = {}  # In-memory fallback if Redis unavailable
        self.timing_cache = {}
        self.ip_cache = {}
        
        # Detection thresholds
        self.SIMILARITY_THRESHOLD = 0.8
        self.SIMULTANEOUS_THRESHOLD = 3  # seconds
        self.TIMING_CORRELATION_THRESHOLD = 0.9
        self.MIN_QUESTIONS_FOR_DETECTION = 3
        
    def get_cache_key(self, quiz_id: int, cache_type: str) -> str:
        """Generate Redis cache key."""
        return f"collab:{cache_type}:{quiz_id}"
    
    def cache_get(self, key: str) -> Optional[str]:
        """Get from Redis or fallback cache."""
        if redis_client:
            try:
                return redis_client.get(key)
            except:
                pass
        return self.answer_cache.get(key)
    
    def cache_set(self, key: str, value: str, expire: int = 3600):
        """Set in Redis or fallback cache."""
        if redis_client:
            try:
                redis_client.setex(key, expire, value)
                return
            except:
                pass
        self.answer_cache[key] = value
    
    def cache_hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field from Redis or fallback."""
        if redis_client:
            try:
                return redis_client.hget(key, field)
            except:
                pass
        cache_dict = self.answer_cache.get(key, {})
        return cache_dict.get(field) if isinstance(cache_dict, dict) else None
    
    def cache_hset(self, key: str, field: str, value: str):
        """Set hash field in Redis or fallback."""
        if redis_client:
            try:
                redis_client.hset(key, field, value)
                return
            except:
                pass
        if key not in self.answer_cache:
            self.answer_cache[key] = {}
        if isinstance(self.answer_cache[key], dict):
            self.answer_cache[key][field] = value
    
    def detect_answer_similarity(self, quiz_id: int, new_answer) -> List[CollaborationSignal]:
        """Detect similar answer patterns between participants."""
        signals = []
        
        try:
            # Get recent answers for this quiz
            recent_answers = Answer.query.filter(
                Answer.quiz_id == quiz_id,
                Answer.created_at >= datetime.utcnow() - timedelta(hours=2)
            ).all()
            
            # Group answers by question and participant
            answers_by_question = defaultdict(list)
            for answer in recent_answers:
                answers_by_question[answer.question_id].append(answer)
            
            # Calculate similarity for participants who answered the same question
            question_answers = answers_by_question.get(new_answer.question_id, [])
            
            for other_answer in question_answers:
                if (other_answer.attempt_id != new_answer.attempt_id and 
                    other_answer.id != new_answer.id):
                    
                    similarity_score = self.calculate_answer_similarity(
                        new_answer, other_answer
                    )
                    
                    if similarity_score >= self.SIMILARITY_THRESHOLD:
                        # Check if these participants have multiple similar answers
                        total_similarity = self.get_total_similarity_score(
                            new_answer.attempt_id, other_answer.attempt_id, quiz_id
                        )
                        
                        if total_similarity >= self.SIMILARITY_THRESHOLD:
                            signal = self.create_collaboration_signal(
                                quiz_id=quiz_id,
                                signal_type='answer_similarity',
                                score=total_similarity,
                                severity=self.get_severity_from_score(total_similarity),
                                participants=[
                                    self.get_user_id_from_attempt(new_answer.attempt_id),
                                    self.get_user_id_from_attempt(other_answer.attempt_id)
                                ],
                                details={
                                    'question_id': new_answer.question_id,
                                    'similarity_score': similarity_score,
                                    'total_questions_compared': self.get_question_count(quiz_id),
                                    'similar_answers_count': self.count_similar_answers(
                                        new_answer.attempt_id, other_answer.attempt_id
                                    )
                                }
                            )
                            signals.append(signal)
            
        except Exception as e:
            print(f"Error in answer similarity detection: {e}")
        
        return signals
    
    def detect_simultaneous_answers(self, quiz_id: int, new_answer) -> List[CollaborationSignal]:
        """Detect participants answering questions simultaneously."""
        signals = []
        
        try:
            # Get recent answers within time threshold
            time_window = datetime.utcnow() - timedelta(seconds=self.SIMULTANEOUS_THRESHOLD)
            simultaneous_answers = Answer.query.filter(
                Answer.quiz_id == quiz_id,
                Answer.question_id == new_answer.question_id,
                Answer.created_at >= time_window,
                Answer.attempt_id != new_answer.attempt_id
            ).all()
            
            if simultaneous_answers:
                participant_ids = [self.get_user_id_from_attempt(new_answer.attempt_id)]
                participant_ids.extend([
                    self.get_user_id_from_attempt(ans.attempt_id) 
                    for ans in simultaneous_answers
                ])
                
                # Remove duplicates
                participant_ids = list(set(participant_ids))
                
                if len(participant_ids) >= 2:
                    # Check if this is a pattern (multiple simultaneous answers)
                    pattern_score = self.check_simultaneous_pattern(
                        quiz_id, participant_ids
                    )
                    
                    signal = self.create_collaboration_signal(
                        quiz_id=quiz_id,
                        signal_type='simultaneous_answers',
                        score=pattern_score,
                        severity=self.get_severity_from_score(pattern_score),
                        participants=participant_ids,
                        details={
                            'question_id': new_answer.question_id,
                            'time_difference_seconds': self.SIMULTANEOUS_THRESHOLD,
                            'participants_count': len(participant_ids),
                            'answer_times': [ans.created_at.isoformat() for ans in simultaneous_answers] + [new_answer.created_at.isoformat()]
                        }
                    )
                    signals.append(signal)
        
        except Exception as e:
            print(f"Error in simultaneous answer detection: {e}")
        
        return signals
    
    def detect_timing_correlation(self, quiz_id: int, new_answer) -> List[CollaborationSignal]:
        """Detect correlated timing patterns between participants."""
        signals = []
        
        try:
            # Get timing data for active attempts
            cache_key = self.get_cache_key(quiz_id, "timing")
            attempt_id = new_answer.attempt_id
            
            # Store timing for this answer
            timing_data = {
                'timestamp': new_answer.created_at.timestamp(),
                'question_id': new_answer.question_id,
                'user_id': self.get_user_id_from_attempt(attempt_id)
            }
            
            self.cache_hset(cache_key, str(attempt_id), json.dumps(timing_data))
            
            # Get all timing data for correlation analysis
            all_timings = self.get_all_attempt_timings(quiz_id)
            
            # Calculate correlations between attempts
            correlations = self.calculate_timing_correlations(all_timings, attempt_id)
            
            for other_attempt_id, correlation in correlations.items():
                if correlation >= self.TIMING_CORRELATION_THRESHOLD:
                    signal = self.create_collaboration_signal(
                        quiz_id=quiz_id,
                        signal_type='timing_correlation',
                        score=correlation,
                        severity=self.get_severity_from_score(correlation),
                        participants=[
                            self.get_user_id_from_attempt(attempt_id),
                            self.get_user_id_from_attempt(other_attempt_id)
                        ],
                        details={
                            'correlation_coefficient': correlation,
                            'questions_analyzed': len(all_timings.get(attempt_id, [])),
                            'time_window_hours': 2
                        }
                    )
                    signals.append(signal)
        
        except Exception as e:
            print(f"Error in timing correlation detection: {e}")
        
        return signals
    
    def detect_shared_ip(self, quiz_id: int, user_id: int) -> List[CollaborationSignal]:
        """Detect participants using same IP address."""
        signals = []
        
        try:
            # Get recent device logs for this quiz
            recent_logs = DeviceLog.query.filter(
                DeviceLog.quiz_id == quiz_id,
                DeviceLog.logged_in_at >= datetime.utcnow() - timedelta(hours=2)
            ).all()
            
            # Group by IP address
            ip_groups = defaultdict(list)
            for log in recent_logs:
                if log.ip_address:
                    ip_groups[log.ip_address].append(log)
            
            # Check for multiple users on same IP
            for ip_address, logs in ip_groups.items():
                user_ids = list(set([log.user_id for log in logs]))
                
                if len(user_ids) >= 2 and user_id in user_ids:
                    # Calculate suspicion score based on timing and behavior
                    suspicion_score = self.calculate_ip_suspicion_score(logs)
                    
                    if suspicion_score >= 0.5:  # Lower threshold for IP sharing
                        signal = self.create_collaboration_signal(
                            quiz_id=quiz_id,
                            signal_type='shared_ip',
                            score=suspicion_score,
                            severity=self.get_severity_from_score(suspicion_score),
                            participants=user_ids,
                            details={
                                'ip_address': ip_address[:8] + "***",  # Anonymized
                                'concurrent_users': len(user_ids),
                                'time_overlap_minutes': self.calculate_time_overlap(logs)
                            }
                        )
                        signals.append(signal)
        
        except Exception as e:
            print(f"Error in shared IP detection: {e}")
        
        return signals
    
    def process_new_answer(self, answer) -> List[CollaborationSignal]:
        """Main entry point for processing new answers."""
        all_signals = []
        
        # Run all detection algorithms
        all_signals.extend(self.detect_answer_similarity(answer.quiz_id, answer))
        all_signals.extend(self.detect_simultaneous_answers(answer.quiz_id, answer))
        all_signals.extend(self.detect_timing_correlation(answer.quiz_id, answer))
        
        # Also check for shared IP when user submits answer
        user_id = self.get_user_id_from_attempt(answer.attempt_id)
        all_signals.extend(self.detect_shared_ip(answer.quiz_id, user_id))
        
        # Save signals to database and emit real-time updates
        for signal in all_signals:
            db.session.add(signal)
            db.session.commit()
            
            # Emit real-time update to proctors
            self.emit_collaboration_update(signal)
        
        return all_signals
    
    def create_collaboration_signal(self, quiz_id: int, signal_type: str, score: float, 
                                  severity: str, participants: List[int], details: dict) -> CollaborationSignal:
        """Create a new collaboration signal."""
        return CollaborationSignal(
            quiz_id=quiz_id,
            signal_type=signal_type,
            score=score,
            severity=severity,
            participants=participants,
            window_start=datetime.utcnow() - timedelta(minutes=5),
            window_end=datetime.utcnow(),
            details=details
        )
    
    def emit_collaboration_update(self, signal: CollaborationSignal):
        """Emit real-time update to proctor dashboard."""
        try:
            room = f"quiz:{signal.quiz_id}"
            update_data = {
                'signal_id': signal.id,
                'type': signal.signal_type,
                'severity': signal.severity,
                'score': signal.score,
                'participants': signal.participants,
                'created_at': signal.created_at.isoformat(),
                'details': signal.details
            }
            
            socketio.emit('collaboration_signal', update_data, room=room, namespace='/collab')
            
        except Exception as e:
            print(f"Error emitting collaboration update: {e}")
    
    # Helper methods
    
    def calculate_answer_similarity(self, answer1, answer2) -> float:
        """Calculate similarity score between two answers."""
        if not answer1.selected_option_id or not answer2.selected_option_id:
            return 0.0
        
        # For multiple choice - exact match gives high score
        if answer1.selected_option_id == answer2.selected_option_id:
            return 1.0
        
        # For text answers, calculate text similarity
        if answer1.text_answer and answer2.text_answer:
            return self.calculate_text_similarity(answer1.text_answer, answer2.text_answer)
        
        return 0.0
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple metrics."""
        if not text1 or not text2:
            return 0.0
        
        # Simple Jaccard similarity for text
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_severity_from_score(self, score: float) -> str:
        """Convert score to severity level."""
        if score >= 0.9:
            return 'high'
        elif score >= 0.7:
            return 'warn'
        else:
            return 'info'
    
    def get_user_id_from_attempt(self, attempt_id: int) -> int:
        """Get user ID from attempt ID."""
        attempt = QuizAttempt.query.get(attempt_id)
        return attempt.participant_id if attempt else 0
    
    def get_total_similarity_score(self, attempt1_id: int, attempt2_id: int, quiz_id: int) -> float:
        """Calculate total similarity score between two attempts."""
        # Check if similarity record exists
        similarity_record = AttemptSimilarity.query.filter_by(
            quiz_id=quiz_id,
            attempt_a_id=min(attempt1_id, attempt2_id),
            attempt_b_id=max(attempt1_id, attempt2_id)
        ).first()
        
        if similarity_record:
            return similarity_record.jaccard_score
        
        # Calculate similarity from scratch
        answers1 = Answer.query.filter_by(attempt_id=attempt1_id).all()
        answers2 = Answer.query.filter_by(attempt_id=attempt2_id).all()
        
        # Group by question
        q1_answers = {a.question_id: a for a in answers1}
        q2_answers = {a.question_id: a for a in answers2}
        
        common_questions = set(q1_answers.keys()) & set(q2_answers.keys())
        
        if len(common_questions) < self.MIN_QUESTIONS_FOR_DETECTION:
            return 0.0
        
        similar_count = 0
        for question_id in common_questions:
            if self.calculate_answer_similarity(q1_answers[question_id], q2_answers[question_id]) >= 0.9:
                similar_count += 1
        
        jaccard_score = similar_count / len(common_questions)
        
        # Store the result
        similarity_record = AttemptSimilarity(
            quiz_id=quiz_id,
            attempt_a_id=min(attempt1_id, attempt2_id),
            attempt_b_id=max(attempt1_id, attempt2_id),
            jaccard_score=jaccard_score,
            coanswer_count=similar_count,
            last_updated=datetime.utcnow()
        )
        
        try:
            db.session.merge(similarity_record)
            db.session.commit()
        except:
            db.session.rollback()
        
        return jaccard_score
    
    def get_question_count(self, quiz_id: int) -> int:
        """Get total number of questions in quiz."""
        from models import Question
        return Question.query.filter_by(quiz_id=quiz_id).count()
    
    def count_similar_answers(self, attempt1_id: int, attempt2_id: int) -> int:
        """Count similar answers between two attempts."""
        similarity = AttemptSimilarity.query.filter_by(
            attempt_a_id=min(attempt1_id, attempt2_id),
            attempt_b_id=max(attempt1_id, attempt2_id)
        ).first()
        
        return similarity.coanswer_count if similarity else 0
    
    def check_simultaneous_pattern(self, quiz_id: int, participant_ids: List[int]) -> float:
        """Check for patterns of simultaneous answers."""
        # Count simultaneous events in recent history
        cache_key = self.get_cache_key(quiz_id, "simultaneous")
        
        # Increment counter for this participant group
        group_key = "-".join(sorted(map(str, participant_ids)))
        current_count = self.cache_hget(cache_key, group_key)
        new_count = int(current_count) + 1 if current_count else 1
        
        self.cache_hset(cache_key, group_key, str(new_count))
        
        # Score based on frequency of simultaneous answers
        return min(1.0, new_count / 5.0)  # Max score after 5 simultaneous events
    
    def get_all_attempt_timings(self, quiz_id: int) -> Dict[int, List[Dict]]:
        """Get timing data for all attempts in quiz."""
        cache_key = self.get_cache_key(quiz_id, "timing")
        timings = {}
        
        if redis_client:
            try:
                timing_data = redis_client.hgetall(cache_key)
                for attempt_id, data_json in timing_data.items():
                    data = json.loads(data_json)
                    attempt_id = int(attempt_id)
                    if attempt_id not in timings:
                        timings[attempt_id] = []
                    timings[attempt_id].append(data)
            except:
                pass
        
        return timings
    
    def calculate_timing_correlations(self, all_timings: Dict[int, List[Dict]], 
                                    current_attempt: int) -> Dict[int, float]:
        """Calculate timing correlations between attempts."""
        correlations = {}
        
        current_timings = all_timings.get(current_attempt, [])
        if len(current_timings) < self.MIN_QUESTIONS_FOR_DETECTION:
            return correlations
        
        for other_attempt, other_timings in all_timings.items():
            if (other_attempt != current_attempt and 
                len(other_timings) >= self.MIN_QUESTIONS_FOR_DETECTION):
                
                correlation = self.calculate_pearson_correlation(
                    current_timings, other_timings
                )
                if correlation >= self.TIMING_CORRELATION_THRESHOLD:
                    correlations[other_attempt] = correlation
        
        return correlations
    
    def calculate_pearson_correlation(self, timings1: List[Dict], timings2: List[Dict]) -> float:
        """Calculate Pearson correlation coefficient for timing patterns."""
        # Simple implementation - could be enhanced
        try:
            if len(timings1) < 2 or len(timings2) < 2:
                return 0.0
            
            # Calculate intervals between answers
            intervals1 = []
            intervals2 = []
            
            for i in range(1, len(timings1)):
                intervals1.append(timings1[i]['timestamp'] - timings1[i-1]['timestamp'])
            
            for i in range(1, len(timings2)):
                intervals2.append(timings2[i]['timestamp'] - timings2[i-1]['timestamp'])
            
            # Use minimum length for comparison
            min_len = min(len(intervals1), len(intervals2))
            if min_len < 2:
                return 0.0
            
            intervals1 = intervals1[:min_len]
            intervals2 = intervals2[:min_len]
            
            # Calculate Pearson correlation
            mean1 = sum(intervals1) / len(intervals1)
            mean2 = sum(intervals2) / len(intervals2)
            
            numerator = sum((x - mean1) * (y - mean2) for x, y in zip(intervals1, intervals2))
            
            sum_sq1 = sum((x - mean1) ** 2 for x in intervals1)
            sum_sq2 = sum((y - mean2) ** 2 for y in intervals2)
            
            denominator = math.sqrt(sum_sq1 * sum_sq2)
            
            return numerator / denominator if denominator > 0 else 0.0
            
        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return 0.0
    
    def calculate_ip_suspicion_score(self, logs: List) -> float:
        """Calculate suspicion score for shared IP usage."""
        # Simple heuristic based on timing overlap and user agent similarity
        user_agents = [log.user_agent for log in logs if log.user_agent]
        unique_agents = set(user_agents)
        
        # If too many different user agents, less suspicious (could be shared network)
        if len(unique_agents) > len(logs) * 0.7:
            return 0.3
        
        # If very similar user agents, more suspicious
        if len(unique_agents) < len(logs) * 0.3:
            return 0.9
        
        return 0.6  # Moderate suspicion for shared IP
    
    def calculate_time_overlap(self, logs: List) -> int:
        """Calculate time overlap in minutes for shared IP logs."""
        if len(logs) < 2:
            return 0
        
        times = [log.logged_in_at for log in logs]
        times.sort()
        
        # Calculate overlap between first and last login
        overlap = (times[-1] - times[0]).total_seconds() / 60
        return int(overlap)


# Global detector instance
detector = CollaborationDetector()