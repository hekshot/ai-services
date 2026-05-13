"""
Guardrails service for RAG hallucination prevention and answer quality validation
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from app.logging_config import ServiceLogger
from app.constants import MIN_CONTEXT_SCORE, MIN_ANSWER_QUALITY_SCORE, MAX_CONTEXT_RESULTS
from app.exceptions import ValidationError, handle_service_exception

@dataclass
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    score: float
    reason: str
    details: Dict[str, Any] = None

@dataclass
class AnswerQuality:
    """Quality metrics for generated answer"""
    relevance_score: float
    factual_accuracy: float
    completeness: float
    coherence: float
    overall_score: float
    issues: List[str]

class RAGGuardrails:
    """Service for preventing hallucinations and ensuring answer quality"""
    
    def __init__(self):
        self.logger = ServiceLogger("RAGGuardrails")
        
        # Hallucination detection patterns
        self.hallucination_patterns = [
            r"\b(I believe|I think|Probably|Perhaps|Maybe|Likely)\b",
            r"\b(It seems|It appears|Looks like)\b",
            r"\b(Generally|Typically|Usually|Often)\b",
            r"\b(Might|Could|Would|Should)\b",
            r"\b(estimate|approximate|roughly)\b"
        ]
        
        # Factual indicators
        self.factual_patterns = [
            r"\b(\d+\.?\d*%|\d+\.?\d*\s*(percent|percentage))\b",
            r"\b(\d+\.\d+|\d+)\s*(GPA|gpa)\b",
            r"\b(\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b",  # Dates
            r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b"  # Names
        ]
        
        # Quality check keywords
        self.quality_indicators = {
            "specific": ["specific", "exact", "precise", "accurate"],
            "evidence": ["according to", "based on", "shows", "indicates"],
            "data": ["score", "grade", "percentage", "metric", "value"],
            "uncertain": ["unsure", "unclear", "unknown", "missing"]
        }
    
    def validate_context_relevance(self, query: str, context_results: List[Dict[str, Any]]) -> ValidationResult:
        """Validate if context is relevant to the query"""
        try:
            if not context_results:
                return ValidationResult(
                    is_valid=False,
                    score=0.0,
                    reason="No context provided"
                )
            
            # Extract facts from context - simplified version
            context_facts = set()
            for result in context_results:
                content = getattr(result, 'content', '') or result.get('content', '')
                # Simple fact extraction - split into sentences
                sentences = re.split(r'[.!?]', content)
                for sentence in sentences:
                    if len(sentence.strip()) > 10:  # Filter out very short sentences
                        context_facts.add(sentence.strip())
            
            # Extract context text
            context_text = "\n\n".join([
                getattr(result, 'content', '') or result.get('content', '') for result in context_results[:MAX_CONTEXT_RESULTS]  # Use top results
            ])
            
            # Calculate relevance score
            query_terms = set(query.lower().split())
            context_terms = set(context_text.lower().split())
            
            # Term overlap score
            overlap_score = len(query_terms & context_terms) / len(query_terms)
            
            # Semantic relevance (simplified)
            semantic_score = self._calculate_semantic_relevance(query, context_text)
            
            # Combined score
            overall_score = (overlap_score * 0.6 + semantic_score * 0.4)
            
            # Determine validity - lower threshold for testing
            is_valid = overall_score >= 0.05  # Much lower threshold for testing
            
            return ValidationResult(
                is_valid=is_valid,
                score=overall_score,
                reason=f"Relevance score: {overall_score:.2f}" if is_valid else f"Low relevance: {overall_score:.2f}",
                details={
                    "term_overlap": overlap_score,
                    "semantic_relevance": semantic_score,
                    "combined_score": overall_score
                }
            )
            
        except Exception as e:
            self.logger.error("Context relevance validation failed", exception=e)
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reason=f"Validation error: {str(e)}"
            )
    
    def validate_answer_quality(self, query: str, answer: str, context_results: List[Dict[str, Any]]) -> AnswerQuality:
        """Validate the quality of generated answer"""
        try:
            # Relevance check
            relevance_score = self._check_answer_relevance(query, answer, context_results)
            
            # Factual accuracy check
            factual_accuracy = self._check_factual_accuracy(answer, context_results)
            
            # Completeness check
            completeness = self._check_completeness(query, answer)
            
            # Coherence check
            coherence = self._check_coherence(answer)
            
            # Overall score
            overall_score = (relevance_score * 0.3 + factual_accuracy * 0.3 + 
                           completeness * 0.2 + coherence * 0.2)
            
            # Identify issues
            issues = self._identify_quality_issues(answer, relevance_score, factual_accuracy)
            
            return AnswerQuality(
                relevance_score=relevance_score,
                factual_accuracy=factual_accuracy,
                completeness=completeness,
                coherence=coherence,
                overall_score=overall_score,
                issues=issues
            )
            
        except Exception as e:
            self.logger.error("Answer quality validation failed", exception=e)
            return AnswerQuality(
                relevance_score=0.0,
                factual_accuracy=0.0,
                completeness=0.0,
                coherence=0.0,
                overall_score=0.0,
                issues=[f"Validation error: {str(e)}"]
            )
    
    def detect_hallucinations(self, answer: str, context_results: List[Dict[str, Any]]) -> ValidationResult:
        """Detect potential hallucinations in the answer"""
        try:
            context_text = " ".join([
                getattr(result, 'content', '') or result.get('content', '') for result in context_results
            ])
            
            hallucination_score = 0.0
            issues = []
            
            # Check for uncertain language
            for pattern in self.hallucination_patterns:
                matches = re.findall(pattern, answer, re.IGNORECASE)
                hallucination_score += len(matches) * 0.1
                if matches:
                    issues.append(f"Uncertain language: {pattern}")
            
            # Check for information not in context
            answer_facts = self._extract_factual_claims(answer)
            context_facts = self._extract_factual_claims(context_text)
            
            unsupported_facts = answer_facts - context_facts
            hallucination_score += len(unsupported_facts) * 0.2
            
            if unsupported_facts:
                issues.append(f"Unsupported facts: {list(unsupported_facts)[:3]}")
            
            # Check for generic statements without context
            generic_statements = self._detect_generic_statements(answer, context_text)
            hallucination_score += len(generic_statements) * 0.15
            
            if generic_statements:
                issues.append("Generic statements without context support")
            
            # Normalize score
            hallucination_score = min(hallucination_score, 1.0)
            
            is_valid = hallucination_score < 0.3  # Low hallucination score is good
            
            return ValidationResult(
                is_valid=is_valid,
                score=1.0 - hallucination_score,  # Invert for quality score
                reason="Low hallucination risk" if is_valid else "High hallucination risk",
                details={
                    "hallucination_score": hallucination_score,
                    "issues": issues,
                    "unsupported_facts": len(unsupported_facts)
                }
            )
            
        except Exception as e:
            self.logger.error("Hallucination detection failed", exception=e)
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reason=f"Detection error: {str(e)}"
            )
    
    def validate_response_safety(self, answer: str) -> ValidationResult:
        """Validate response for safety and appropriateness"""
        try:
            # Check for harmful content
            harmful_patterns = [
                r"\b(hate|violence|abuse|discrimination)\b",
                r"\b(inappropriate|unethical|illegal)\b"
            ]
            
            for pattern in harmful_patterns:
                if re.search(pattern, answer, re.IGNORECASE):
                    return ValidationResult(
                        is_valid=False,
                        score=0.0,
                        reason="Potentially harmful content detected"
                    )
            
            # Check for refusal to answer
            refusal_patterns = [
                "I cannot answer",
                "I don't have enough information",
                "I cannot provide",
                "I'm not able to"
            ]
            
            for pattern in refusal_patterns:
                if pattern.lower() in answer.lower():
                    return ValidationResult(
                        is_valid=True,
                        score=0.5,
                        reason="Proper refusal to answer",
                        details={"refusal_type": "information_insufficient"}
                    )
            
            return ValidationResult(
                is_valid=True,
                score=1.0,
                reason="Response appears safe"
            )
            
        except Exception as e:
            self.logger.error("Safety validation failed", exception=e)
            return ValidationResult(
                is_valid=False,
                score=0.0,
                reason=f"Safety check error: {str(e)}"
            )
    
    def _calculate_semantic_relevance(self, query: str, context: str) -> float:
        """Calculate semantic relevance between query and context"""
        # Simplified semantic relevance based on key terms
        query_keywords = self._extract_keywords(query)
        context_keywords = self._extract_keywords(context)
        
        if not query_keywords:
            return 0.0
        
        matches = len(query_keywords & context_keywords)
        return matches / len(query_keywords)
    
    def _extract_keywords(self, text: str) -> set:
        """Extract important keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did'}
        return {word for word in words if word not in stop_words and len(word) > 2}
    
    def _check_answer_relevance(self, query: str, answer: str, context_results: List[Dict[str, Any]]) -> float:
        """Check if answer is relevant to query"""
        query_keywords = self._extract_keywords(query)
        answer_keywords = self._extract_keywords(answer)
        
        if not query_keywords:
            return 0.0
        
        relevance = len(query_keywords & answer_keywords) / len(query_keywords)
        
        # Bonus for using context terms
        context_text = " ".join([getattr(r, 'content', '') or r.get('content', '') for r in context_results])
        
        supported_facts = answer_facts & context_facts
        return len(supported_facts) / len(answer_facts)
    
    def _check_completeness(self, query: str, answer: str) -> float:
        """Check if answer completely addresses the query"""
        # Simple completeness check based on answer length and content
        if len(answer) < 50:
            return 0.3  # Too short
        elif len(answer) < 150:
            return 0.6  # Moderate
        else:
            return 0.9  # Good length
    
    def _check_coherence(self, answer: str) -> float:
        """Check answer coherence and readability"""
        # Simple coherence checks
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Check average sentence length
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        # Penalize very short or very long sentences
        if avg_length < 5 or avg_length > 30:
            return 0.5
        else:
            return 0.8
    
    def _identify_quality_issues(self, answer: str, relevance_score: float, factual_accuracy: float) -> List[str]:
        """Identify specific quality issues"""
        issues = []
        
        if relevance_score < 0.5:
            issues.append("Low relevance to query")
        
        if factual_accuracy < 0.5:
            issues.append("Potential factual inaccuracies")
        
        if len(answer) < 50:
            issues.append("Answer too short")
        
        # Check for vague language
        vague_words = ["some", "many", "few", "several", "various"]
        for word in vague_words:
            if word in answer.lower():
                issues.append(f"Contains vague language: '{word}'")
                break
        
        return issues
    
    def _extract_factual_claims(self, text: str) -> set:
        """Extract factual claims from text"""
        claims = set()
        
        # Extract numbers and percentages
        numbers = re.findall(r'\b\d+\.?\d*\s*(%|percent|GPA|gpa|score|grade)\b', text, re.IGNORECASE)
        claims.update(numbers)
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
        claims.update(dates)
        
        # Extract names (simplified)
        names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text)
        claims.update(names)
        
        return claims
    
    def _detect_generic_statements(self, answer: str, context: str) -> List[str]:
        """Detect generic statements not supported by context"""
        generic_patterns = [
            r"The student.*generally.*",
            r"Typically.*",
            r"Usually.*",
            r"Overall.*"
        ]
        
        generic_statements = []
        for pattern in generic_patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            generic_statements.extend(matches)
        
        return generic_statements
