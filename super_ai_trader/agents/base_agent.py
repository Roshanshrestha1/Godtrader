"""
Super AI Trader - Base Agent Module
Abstract base class for all trading agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import pandas as pd


class SignalResult:
    """Represents a trading signal from an agent."""
    
    def __init__(self, signal: str, confidence: float, reasons: list, score: float = 0):
        self.signal = signal  # 'BUY', 'SELL', 'NEUTRAL', 'NO_TRADE'
        self.confidence = confidence  # 0-100
        self.reasons = reasons  # List of reason strings
        self.score = score  # Raw score before conversion to signal
    
    def to_dict(self) -> dict:
        return {
            'signal': self.signal,
            'confidence': self.confidence,
            'reasons': self.reasons,
            'score': self.score
        }
    
    def __repr__(self):
        return f"SignalResult(signal={self.signal}, confidence={self.confidence}%, score={self.score})"


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    Each agent implements specific trading rules and returns signals.
    """
    
    def __init__(self, name: str, description: str, module_ids: list):
        self.name = name
        self.description = description
        self.module_ids = module_ids
        self.enabled = True
    
    @abstractmethod
    def analyze(self, data: Dict[int, pd.DataFrame], current_price: dict) -> SignalResult:
        """
        Analyze market data and return a trading signal.
        
        Args:
            data: Dictionary of DataFrames keyed by timeframe (1, 5, 60, 240 minutes)
            current_price: Current price information
        
        Returns:
            SignalResult object with signal, confidence, and reasons
        """
        pass
    
    def get_info(self) -> dict:
        """Return agent information."""
        return {
            'name': self.name,
            'description': self.description,
            'modules': self.module_ids,
            'enabled': self.enabled
        }
    
    def enable(self):
        """Enable this agent."""
        self.enabled = True
    
    def disable(self):
        """Disable this agent."""
        self.enabled = False
    
    def _calculate_confidence(self, score: float, max_score: float, base_confidence: float = 50) -> float:
        """
        Calculate confidence percentage from raw score.
        
        Args:
            score: Raw score from rule evaluation
            max_score: Maximum possible absolute score
            base_confidence: Base confidence level
        
        Returns:
            Confidence percentage (0-100)
        """
        if max_score == 0:
            return base_confidence
        
        confidence = base_confidence + (abs(score) / max_score) * 50
        return min(max(confidence, 0), 100)
    
    def _get_latest_values(self, df: pd.DataFrame, column: str, num_bars: int = 1) -> any:
        """Safely get latest value(s) from a dataframe column."""
        if df is None or column not in df.columns:
            return None
        
        if num_bars == 1:
            return df[column].iloc[-1] if len(df) > 0 else None
        else:
            return df[column].iloc[-num_bars:].tolist() if len(df) >= num_bars else None
    
    def _get_previous_values(self, df: pd.DataFrame, column: str, num_bars: int = 1) -> any:
        """Safely get previous value(s) from a dataframe column."""
        if df is None or column not in df.columns:
            return None
        
        idx = -num_bars - 1
        if abs(idx) > len(df):
            return None
        
        if num_bars == 1:
            return df[column].iloc[idx]
        else:
            return df[column].iloc[idx:idx+num_bars].tolist()
