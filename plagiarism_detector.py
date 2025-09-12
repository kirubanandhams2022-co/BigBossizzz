"""
AI-Powered Plagiarism Detection Service for BigBossizzz Platform

This service uses multiple machine learning algorithms to detect plagiarism in text submissions:
- TF-IDF Vectorization with Cosine Similarity
- Jaccard Similarity for set-based comparison
- Levenshtein Distance for string similarity  
- N-gram analysis for structural patterns
"""

import re
import string
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime

import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textdistance

from app import db
from models import PlagiarismAnalysis, PlagiarismMatch, Answer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlagiarismDetector:
    """Advanced AI-powered plagiarism detection system"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 3),
            lowercase=True,
            strip_accents='unicode'
        )
        
        # Risk thresholds for different algorithms
        self.thresholds = {
            'cosine_high': 0.8,
            'cosine_medium': 0.6,
            'cosine_low': 0.4,
            'jaccard_high': 0.7,
            'jaccard_medium': 0.5,
            'jaccard_low': 0.3,
            'levenshtein_high': 0.85,
            'levenshtein_medium': 0.7,
            'levenshtein_low': 0.5
        }
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        if not text:
            return ""
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:]', '', text)
        
        # Convert to lowercase
        text = text.lower()
        
        return text
    
    def extract_ngrams(self, text: str, n: int = 3) -> set:
        """Extract n-grams from text for structural analysis"""
        words = text.split()
        ngrams = set()
        
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i:i+n])
            ngrams.add(ngram)
            
        return ngrams
    
    def calculate_cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity using TF-IDF vectors"""
        try:
            corpus = [text1, text2]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity coefficient"""
        try:
            set1 = set(text1.split())
            set2 = set(text2.split())
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            if union == 0:
                return 0.0
                
            return intersection / union
        except Exception as e:
            logger.error(f"Error calculating Jaccard similarity: {e}")
            return 0.0
    
    def calculate_levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Calculate normalized Levenshtein similarity"""
        try:
            distance = textdistance.levenshtein(text1, text2)
            max_len = max(len(text1), len(text2))
            
            if max_len == 0:
                return 1.0
                
            similarity = 1 - (distance / max_len)
            return max(0.0, similarity)
        except Exception as e:
            logger.error(f"Error calculating Levenshtein similarity: {e}")
            return 0.0
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using n-gram overlap"""
        try:
            ngrams1 = self.extract_ngrams(text1)
            ngrams2 = self.extract_ngrams(text2)
            
            if not ngrams1 or not ngrams2:
                return 0.0
                
            intersection = len(ngrams1.intersection(ngrams2))
            union = len(ngrams1.union(ngrams2))
            
            return intersection / union if union > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def determine_risk_level(self, cosine: float, jaccard: float, levenshtein: float, semantic: float) -> Tuple[str, float, float]:
        """Determine overall risk level and confidence"""
        
        # Calculate weighted overall score
        weights = {
            'cosine': 0.4,      # Strongest indicator for academic plagiarism
            'jaccard': 0.25,    # Good for exact word matches
            'levenshtein': 0.2, # Character-level similarity
            'semantic': 0.15    # Structural patterns
        }
        
        overall_score = (
            cosine * weights['cosine'] +
            jaccard * weights['jaccard'] +
            levenshtein * weights['levenshtein'] +
            semantic * weights['semantic']
        )
        
        # Determine risk level
        if overall_score >= 0.75:
            risk_level = 'critical'
        elif overall_score >= 0.60:
            risk_level = 'high'
        elif overall_score >= 0.40:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Calculate confidence based on algorithm agreement
        scores = [cosine, jaccard, levenshtein, semantic]
        score_variance = float(np.var(scores))
        confidence = 1.0 - min(score_variance, 1.0)  # Lower variance = higher confidence
        
        return risk_level, overall_score, confidence
    
    def find_matching_segments(self, text1: str, text2: str, threshold: float = 0.8) -> List[Dict]:
        """Find specific text segments that match between two texts"""
        matches = []
        
        # Split into sentences for more granular analysis
        sentences1 = nltk.sent_tokenize(text1)
        sentences2 = nltk.sent_tokenize(text2)
        
        for i, sent1 in enumerate(sentences1):
            for j, sent2 in enumerate(sentences2):
                similarity = self.calculate_cosine_similarity(sent1, sent2)
                
                if similarity >= threshold:
                    match = {
                        'similarity': similarity,
                        'text1_segment': sent1,
                        'text2_segment': sent2,
                        'text1_position': text1.find(sent1),
                        'text2_position': text2.find(sent2),
                        'match_type': self._classify_match_type(sent1, sent2, similarity)
                    }
                    matches.append(match)
        
        return matches
    
    def _classify_match_type(self, text1: str, text2: str, similarity: float) -> str:
        """Classify the type of match found"""
        if similarity >= 0.95:
            return 'exact'
        elif similarity >= 0.8:
            # Check if it's just paraphrasing
            jaccard = self.calculate_jaccard_similarity(text1, text2)
            if jaccard >= 0.7:
                return 'paraphrase'
            else:
                return 'structural'
        else:
            return 'semantic'
    
    def analyze_text_for_plagiarism(self, target_text: str, comparison_texts: List[Tuple[int, str]], answer_id: int, quiz_attempt_id: int, question_id: int) -> PlagiarismAnalysis:
        """
        Analyze target text against a corpus of comparison texts for plagiarism
        
        Args:
            target_text: The text to analyze
            comparison_texts: List of tuples (answer_id, text) to compare against
            answer_id: ID of the answer being analyzed
            quiz_attempt_id: ID of the quiz attempt
            question_id: ID of the question
            
        Returns:
            PlagiarismAnalysis object with results
        """
        
        logger.info(f"Starting plagiarism analysis for answer {answer_id}")
        
        # Preprocess target text
        clean_target = self.preprocess_text(target_text)
        
        if not clean_target.strip():
            logger.warning(f"Empty text for answer {answer_id}")
            # Create analysis for empty text
            analysis = PlagiarismAnalysis()
            analysis.quiz_attempt_id = quiz_attempt_id
            analysis.question_id = question_id
            analysis.answer_id = answer_id
            analysis.overall_similarity_score = 0.0
            analysis.risk_level = 'low'
            analysis.cosine_similarity = 0.0
            analysis.jaccard_similarity = 0.0
            analysis.levenshtein_similarity = 0.0
            analysis.semantic_similarity = 0.0
            analysis.analyzed_text = target_text
            analysis.confidence_score = 1.0
            analysis.is_flagged = False
            analysis.requires_review = False
            return analysis
        
        max_similarities = {
            'cosine': 0.0,
            'jaccard': 0.0,
            'levenshtein': 0.0,
            'semantic': 0.0
        }
        
        all_matches = []
        
        # Compare against all provided texts
        for comp_answer_id, comp_text in comparison_texts:
            if comp_answer_id == answer_id:  # Skip self-comparison
                continue
                
            clean_comp = self.preprocess_text(comp_text)
            
            if not clean_comp.strip():
                continue
            
            # Calculate all similarity metrics
            cosine_sim = self.calculate_cosine_similarity(clean_target, clean_comp)
            jaccard_sim = self.calculate_jaccard_similarity(clean_target, clean_comp)
            levenshtein_sim = self.calculate_levenshtein_similarity(clean_target, clean_comp)
            semantic_sim = self.calculate_semantic_similarity(clean_target, clean_comp)
            
            # Track maximum similarities
            max_similarities['cosine'] = max(max_similarities['cosine'], cosine_sim)
            max_similarities['jaccard'] = max(max_similarities['jaccard'], jaccard_sim)
            max_similarities['levenshtein'] = max(max_similarities['levenshtein'], levenshtein_sim)
            max_similarities['semantic'] = max(max_similarities['semantic'], semantic_sim)
            
            # Find specific matching segments if similarity is high
            if cosine_sim >= 0.6:  # Only store matches above threshold
                segments = self.find_matching_segments(clean_target, clean_comp, threshold=0.6)
                
                for segment in segments:
                    match = PlagiarismMatch()
                    match.matched_against_id = comp_answer_id
                    match.similarity_score = segment['similarity']
                    match.match_type = segment['match_type']
                    match.matched_text_segment = segment['text1_segment']
                    match.original_text_segment = segment['text2_segment']
                    match.start_position = segment['text1_position']
                    match.end_position = segment['text1_position'] + len(segment['text1_segment'])
                    match.algorithm_used = 'tfidf_cosine'
                    match.confidence = cosine_sim
                    all_matches.append(match)
        
        # Determine overall risk and confidence
        risk_level, overall_score, confidence = self.determine_risk_level(
            max_similarities['cosine'],
            max_similarities['jaccard'],
            max_similarities['levenshtein'],
            max_similarities['semantic']
        )
        
        # Determine if flagging is needed
        is_flagged = risk_level in ['high', 'critical']
        requires_review = risk_level in ['medium', 'high', 'critical']
        
        # Create plagiarism analysis record
        analysis = PlagiarismAnalysis()
        analysis.quiz_attempt_id = quiz_attempt_id
        analysis.question_id = question_id
        analysis.answer_id = answer_id
        analysis.overall_similarity_score = overall_score
        analysis.risk_level = risk_level
        analysis.cosine_similarity = max_similarities['cosine']
        analysis.jaccard_similarity = max_similarities['jaccard']
        analysis.levenshtein_similarity = max_similarities['levenshtein']
        analysis.semantic_similarity = max_similarities['semantic']
        analysis.analyzed_text = target_text
        analysis.confidence_score = confidence
        analysis.is_flagged = is_flagged
        analysis.requires_review = requires_review
        
        # Save analysis first to get ID
        db.session.add(analysis)
        db.session.flush()
        
        # Add matches to analysis
        for match in all_matches:
            match.analysis_id = analysis.id
            db.session.add(match)
        
        logger.info(f"Plagiarism analysis completed for answer {answer_id}: {risk_level} risk ({overall_score:.3f} similarity)")
        
        return analysis

# Global instance for use throughout the application
plagiarism_detector = PlagiarismDetector()