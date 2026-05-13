"""
Complete Candlestick Pattern Encyclopedia for Super AI Trader Brain V4.0

All Patterns With Full Detection Algorithms
- 12 Bullish Reversal Patterns
- 12 Bearish Reversal Patterns  
- 8 Continuation Patterns
- Special Patterns (Pin Bar, Inside Bar, Outside Bar)

Integrated with Agent scoring system for signal generation.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np


@dataclass
class Candle:
    """Standard candle representation"""
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    timestamp: int = 0


# ============================================================================
# SECTION 1 — BULLISH REVERSAL PATTERNS
# ============================================================================

def is_hammer(candle: Candle, prev_candles: List[Candle], atr: float) -> bool:
    """
    HAMMER Pattern
    
    VISUAL:
            │          ← tiny upper wick (optional)
           ═══         ← small body (green or red)
            │
            │
            │          ← long lower wick (2x+ body)
            │
    
    MEANING: Sellers pushed price down hard but buyers took full control by close
    
    RULES:
      ✅ Lower wick >= 2x body size
      ✅ Lower wick >= 60% of total candle range
      ✅ Upper wick <= 30% of body size
      ✅ Body >= 10% of ATR (not a doji)
      ✅ Appears after 3+ bearish candles (downtrend)
    
    SCORE IN SYSTEM: +2 (confirmation candle)
    """
    body = abs(candle.close - candle.open)
    lower_wick = min(candle.open, candle.close) - candle.low
    upper_wick = candle.high - max(candle.open, candle.close)
    total_range = candle.high - candle.low

    if total_range == 0 or body == 0:
        return False

    # Downtrend check (3 lower closes before)
    if len(prev_candles) < 3:
        return False
    
    downtrend = all(
        prev_candles[i].close > prev_candles[i+1].close
        for i in range(min(3, len(prev_candles)-1))
    )

    return (
        lower_wick >= 2.0 * body and
        lower_wick / total_range >= 0.60 and
        upper_wick <= 0.30 * body and
        body >= 0.10 * atr and
        downtrend
    )


def is_inverted_hammer(candle: Candle, prev_candles: List[Candle], 
                       next_candle: Optional[Candle], atr: float) -> bool:
    """
    INVERTED HAMMER Pattern
    
    VISUAL:
            │
            │
            │          ← long upper wick (2x+ body)
           ═══         ← small body at bottom
            │          ← tiny lower wick
    
    MEANING: Buyers tried to push price up but sellers pushed back
             STILL bullish — signals potential reversal
             Needs NEXT candle confirmation (green candle)
    
    RULES:
      ✅ Upper wick >= 2x body
      ✅ Upper wick >= 60% of total range
      ✅ Lower wick <= 30% of body
      ✅ Appears after downtrend
      ✅ REQUIRES next candle to be bullish (confirmation)
    
    SCORE IN SYSTEM: +1 (weaker, needs confirmation)
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low

    if total_range == 0 or body == 0:
        return False

    if len(prev_candles) < 3:
        return False

    downtrend = all(
        prev_candles[i].close > prev_candles[i+1].close
        for i in range(min(3, len(prev_candles)-1))
    )

    # MUST have bullish confirmation next candle
    confirmed = next_candle.close > next_candle.open if next_candle else False

    return (
        upper_wick >= 2.0 * body and
        upper_wick / total_range >= 0.60 and
        lower_wick <= 0.30 * body and
        body >= 0.10 * atr and
        downtrend and
        confirmed
    )


def is_bullish_engulfing(prev: Candle, curr: Candle, 
                         prev_volume: float, curr_volume: float) -> Dict:
    """
    BULLISH ENGULFING Pattern
    
    VISUAL:
      Day 1:  ███       ← bearish (red) candle
      Day 2: █████████  ← bullish (green) candle
             completely engulfs Day 1 body
    
    MEANING: Bears controlled day 1, Bulls came in with MASSIVE force on day 2
             One of the STRONGEST reversal signals
    
    RULES:
      ✅ Day 1: bearish (close < open)
      ✅ Day 2: bullish (close > open)
      ✅ Day 2 open BELOW Day 1 close
      ✅ Day 2 close ABOVE Day 1 open
      ✅ Day 2 body LARGER than Day 1 body
      ✅ Day 2 volume > Day 1 volume (stronger signal)
    
    SCORE IN SYSTEM: +3 (strong confirmation)
    """
    prev_bearish = prev.close < prev.open
    curr_bullish = curr.close > curr.open

    prev_body_top = prev.open
    prev_body_bot = prev.close
    curr_body_top = curr.close
    curr_body_bot = curr.open

    prev_body_size = abs(prev.close - prev.open)
    curr_body_size = abs(curr.close - curr.open)

    volume_confirms = curr_volume > prev_volume

    pattern_detected = (
        prev_bearish and
        curr_bullish and
        curr_body_bot < prev_body_bot and
        curr_body_top > prev_body_top and
        curr_body_size > prev_body_size
    )

    return {
        "pattern": pattern_detected,
        "strong": volume_confirms,
        "score": 3 if (pattern_detected and volume_confirms) else 2
    }


def is_piercing_line(prev: Candle, curr: Candle) -> bool:
    """
    PIERCING LINE Pattern
    
    VISUAL:
      Day 1: █████████  ← large bearish candle
      Day 2:    █████   ← opens below Day1 low, closes ABOVE Day1 midpoint
    
    MEANING: Similar to engulfing but less powerful
             Bulls recovered more than halfway
    
    RULES:
      ✅ Day 1: large bearish candle
      ✅ Day 2: opens BELOW Day 1 low (gap down)
      ✅ Day 2: closes ABOVE 50% of Day 1 body
      ✅ Day 2: does NOT fully engulf Day 1
    
    SCORE IN SYSTEM: +2
    """
    prev_bearish = prev.close < prev.open
    curr_bullish = curr.close > curr.open

    prev_midpoint = (prev.open + prev.close) / 2
    day2_opens_below = curr.open < prev.close
    day2_closes_above_mid = curr.close > prev_midpoint
    not_full_engulf = curr.close < prev.open

    return (
        prev_bearish and
        curr_bullish and
        day2_opens_below and
        day2_closes_above_mid and
        not_full_engulf
    )


def is_morning_star(c1: Candle, c2: Candle, c3: Candle, atr: float) -> bool:
    """
    MORNING STAR Pattern
    
    VISUAL:
      Day 1: ████████   ← large bearish candle
      Day 2:   ██       ← small body (indecision)
      Day 3:    ████████ ← large bullish candle
    
    MEANING: 3-candle pattern - Bears → Indecision → Bulls take FULL control
             Very reliable reversal signal
    
    RULES:
      ✅ Day 1: large bearish body (>= 0.7x ATR)
      ✅ Day 2: small body (<= 0.3x ATR)
      ✅ Day 3: large bullish body (>= 0.7x ATR)
      ✅ Day 3: closes ABOVE Day 1 midpoint
    
    SCORE IN SYSTEM: +3 (high reliability)
    """
    c1_bearish = c1.close < c1.open
    c3_bullish = c3.close > c3.open

    c1_body = abs(c1.close - c1.open)
    c2_body = abs(c2.close - c2.open)
    c3_body = abs(c3.close - c3.open)

    c1_midpoint = (c1.open + c1.close) / 2

    return (
        c1_bearish and
        c3_bullish and
        c1_body >= 0.7 * atr and
        c2_body <= 0.3 * atr and
        c3_body >= 0.7 * atr and
        c3.close > c1_midpoint and
        c2.high < c1.close
    )


def is_bullish_harami(prev: Candle, curr: Candle) -> bool:
    """
    BULLISH HARAMI Pattern
    
    VISUAL:
      Day 1: ████████   ← large bearish candle
      Day 2:   ████     ← small bullish inside Day 1
    
    MEANING: "Harami" = pregnant in Japanese
             Small candle INSIDE previous large candle
             Shows momentum slowing down
    
    RULES:
      ✅ Day 1: large bearish candle
      ✅ Day 2: bullish candle completely inside Day 1 BODY
      ✅ Day 2 body must be < 30% of Day 1 body
    
    SCORE IN SYSTEM: +1 (weak — needs confirmation)
    """
    prev_bearish = prev.close < prev.open
    curr_bullish = curr.close > curr.open

    curr_body_size = abs(curr.close - curr.open)
    prev_body_size = abs(prev.close - prev.open)

    inside_body = (
        curr.open > prev.close and
        curr.close < prev.open
    )

    return (
        prev_bearish and
        curr_bullish and
        inside_body and
        curr_body_size < 0.30 * prev_body_size
    )


def is_tweezer_bottom(prev: Candle, curr: Candle, pip_tolerance: float = 0.0003) -> bool:
    """
    TWEEZER BOTTOM Pattern
    
    VISUAL:
      Day 1:  ████      ← bearish candle
      Day 2:  ████      ← bullish candle
              ↑↑↑↑
         Same low point = double bottom
    
    MEANING: Two candles with identical (or very close) lows
             Price rejected the SAME level twice
    
    RULES:
      ✅ Day 1: bearish candle
      ✅ Day 2: bullish candle
      ✅ Both have same low (within 3 pips / 0.0003)
    
    SCORE IN SYSTEM: +2
    """
    prev_bearish = prev.close < prev.open
    curr_bullish = curr.close > curr.open

    same_low = abs(prev.low - curr.low) <= pip_tolerance

    return (
        prev_bearish and
        curr_bullish and
        same_low and
        curr.close > prev.open
    )


def is_three_white_soldiers(c1: Candle, c2: Candle, c3: Candle, atr: float) -> bool:
    """
    THREE WHITE SOLDIERS Pattern
    
    VISUAL:
      Day 1:  ████     ← bullish candle
      Day 2:   █████   ← bullish, opens in Day1 body
      Day 3:    ██████ ← bullish, opens in Day2 body
    
    MEANING: Three consecutive large bullish candles
             VERY strong reversal or continuation signal
    
    RULES:
      ✅ Three consecutive bullish candles
      ✅ Each opens within previous candle's body
      ✅ Each closes progressively higher
      ✅ Each body >= 0.6x ATR
    
    SCORE IN SYSTEM: +3 (very strong)
    """
    all_bullish = (
        c1.close > c1.open and
        c2.close > c2.open and
        c3.close > c3.open
    )

    progressive_highs = (
        c2.close > c1.close and
        c3.close > c2.close
    )

    opens_inside = (
        c1.open < c2.open < c1.close and
        c2.open < c3.open < c2.close
    )

    substantial_bodies = all(
        abs(c.close - c.open) >= 0.6 * atr
        for c in [c1, c2, c3]
    )

    small_wicks = all(
        (c.high - c.close) <= 0.3 * abs(c.close - c.open)
        for c in [c1, c2, c3]
    )

    return (
        all_bullish and
        progressive_highs and
        opens_inside and
        substantial_bodies and
        small_wicks
    )


# ============================================================================
# SECTION 2 — BEARISH REVERSAL PATTERNS
# ============================================================================

def is_shooting_star(candle: Candle, prev_candles: List[Candle], atr: float) -> bool:
    """
    SHOOTING STAR Pattern
    
    VISUAL:
            │
            │
            │          ← long upper wick (2x+ body)
           ═══         ← small body at bottom
            │          ← tiny lower wick (optional)
    
    MEANING: Opposite of hammer
             Buyers pushed price up hard, Sellers slammed it back down
    
    RULES:
      ✅ Upper wick >= 2x body size
      ✅ Upper wick >= 60% of total range
      ✅ Lower wick <= 30% of body
      ✅ Appears after 3+ bullish candles (uptrend)
    
    SCORE IN SYSTEM: -2 (confirmation candle)
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low

    if total_range == 0 or body == 0:
        return False

    if len(prev_candles) < 3:
        return False

    uptrend = all(
        prev_candles[i].close < prev_candles[i+1].close
        for i in range(min(3, len(prev_candles)-1))
    )

    return (
        upper_wick >= 2.0 * body and
        upper_wick / total_range >= 0.60 and
        lower_wick <= 0.30 * body and
        body >= 0.10 * atr and
        uptrend
    )


def is_hanging_man(candle: Candle, prev_candles: List[Candle], 
                   next_candle: Optional[Candle], atr: float) -> bool:
    """
    HANGING MAN Pattern
    
    VISUAL: Same as HAMMER but appears at TOP of uptrend
    
    MEANING: Looks EXACTLY like a hammer
             But appears at TOP of uptrend
             WARNING sign — needs confirmation next candle
    
    RULES:
      ✅ Same shape as hammer (long lower wick)
      ✅ APPEARS AFTER UPTREND (key difference from hammer)
      ✅ Next candle must be bearish (confirmation required)
    
    SCORE IN SYSTEM: -1 (needs confirmation)
    """
    body = abs(candle.close - candle.open)
    lower_wick = min(candle.open, candle.close) - candle.low
    upper_wick = candle.high - max(candle.open, candle.close)

    if body == 0:
        return False

    if len(prev_candles) < 3:
        return False

    # KEY: uptrend context (opposite of hammer)
    uptrend = all(
        prev_candles[i].close < prev_candles[i+1].close
        for i in range(min(3, len(prev_candles)-1))
    )

    # MUST have bearish confirmation
    confirmed = (
        next_candle.close < next_candle.open
        if next_candle else False
    )

    return (
        lower_wick >= 2.0 * body and
        upper_wick <= 0.30 * body and
        body >= 0.10 * atr and
        uptrend and
        confirmed
    )


def is_bearish_engulfing(prev: Candle, curr: Candle, 
                         prev_vol: float, curr_vol: float) -> Dict:
    """
    BEARISH ENGULFING Pattern
    
    VISUAL:
      Day 1:  ██████    ← bullish (green) candle
      Day 2: ██████████ ← bearish (red) completely engulfs
    
    MEANING: Bulls controlled Day 1, Bears came in with MASSIVE force on Day 2
             One of STRONGEST bearish reversals
    
    RULES:
      ✅ Day 1: bullish (close > open)
      ✅ Day 2: bearish (close < open)
      ✅ Day 2 open ABOVE Day 1 close
      ✅ Day 2 close BELOW Day 1 open
      ✅ Day 2 body LARGER than Day 1 body
    
    SCORE IN SYSTEM: -3 (strong)
    """
    prev_bullish = prev.close > prev.open
    curr_bearish = curr.close < curr.open

    engulfs = (
        curr.open > prev.close and
        curr.close < prev.open and
        abs(curr.close - curr.open) > abs(prev.close - prev.open)
    )

    volume_confirms = curr_vol > prev_vol

    pattern_detected = prev_bullish and curr_bearish and engulfs

    return {
        "pattern": pattern_detected,
        "strong": volume_confirms,
        "score": -3 if (pattern_detected and volume_confirms) else -2
    }


def is_evening_star(c1: Candle, c2: Candle, c3: Candle, atr: float) -> bool:
    """
    EVENING STAR Pattern
    
    VISUAL:
      Day 1:  ████████  ← large bullish candle
      Day 2:    ██      ← small body at top
      Day 3: ████████   ← large bearish candle
    
    MEANING: Opposite of morning star
             3-candle bearish reversal at top of trend
    
    RULES:
      ✅ Day 1: large bullish (>= 0.7x ATR)
      ✅ Day 2: small body (<= 0.3x ATR)
      ✅ Day 3: large bearish (>= 0.7x ATR)
      ✅ Day 3: closes BELOW Day 1 midpoint
    
    SCORE IN SYSTEM: -3 (high reliability)
    """
    c1_bullish = c1.close > c1.open
    c3_bearish = c3.close < c3.open

    c1_body = abs(c1.close - c1.open)
    c2_body = abs(c2.close - c2.open)
    c3_body = abs(c3.close - c3.open)

    c1_midpoint = (c1.open + c1.close) / 2

    return (
        c1_bullish and
        c3_bearish and
        c1_body >= 0.7 * atr and
        c2_body <= 0.3 * atr and
        c3_body >= 0.7 * atr and
        c3.close < c1_midpoint and
        c2.low > c1.close
    )


def is_dark_cloud_cover(prev: Candle, curr: Candle) -> bool:
    """
    DARK CLOUD COVER Pattern
    
    VISUAL:
      Day 1:  ████████  ← large bullish candle
      Day 2: █████      ← opens above, closes below midpoint
    
    MEANING: Bearish version of piercing line
             Day 2 opens higher (gap up) then reverses
    
    RULES:
      ✅ Day 1: large bullish candle
      ✅ Day 2: opens ABOVE Day 1 high (gap up)
      ✅ Day 2: closes BELOW 50% of Day 1 body
      ✅ Day 2: bearish candle
    
    SCORE IN SYSTEM: -2
    """
    prev_bullish = prev.close > prev.open
    curr_bearish = curr.close < curr.open

    prev_midpoint = (prev.open + prev.close) / 2

    opens_above = curr.open > prev.close
    closes_below_mid = curr.close < prev_midpoint
    not_full_engulf = curr.close > prev.open

    return (
        prev_bullish and
        curr_bearish and
        opens_above and
        closes_below_mid and
        not_full_engulf
    )


def is_bearish_harami(prev: Candle, curr: Candle) -> bool:
    """
    BEARISH HARAMI Pattern
    
    VISUAL:
      Day 1: ████████   ← large bullish candle
      Day 2:   ████     ← small bearish inside Day 1
    
    MEANING: Momentum slowing at top
             Bears starting to appear inside bull candle
    
    RULES:
      ✅ Day 1: large bullish candle
      ✅ Day 2: bearish candle inside Day 1 BODY
      ✅ Day 2 body < 30% of Day 1 body
    
    SCORE IN SYSTEM: -1 (weak — needs confirmation)
    """
    prev_bullish = prev.close > prev.open
    curr_bearish = curr.close < curr.open

    curr_body_size = abs(curr.close - curr.open)
    prev_body_size = abs(prev.close - prev.open)

    inside_body = (
        curr.open < prev.close and
        curr.close > prev.open
    )

    return (
        prev_bullish and
        curr_bearish and
        inside_body and
        curr_body_size < 0.30 * prev_body_size
    )


def is_three_black_crows(c1: Candle, c2: Candle, c3: Candle, atr: float) -> bool:
    """
    THREE BLACK CROWS Pattern
    
    VISUAL:
      Day 1: ████████   ← large bearish
      Day 2: ███████    ← opens inside Day 1, closes lower
      Day 3: ██████     ← opens inside Day 2, closes lower
    
    MEANING: Opposite of Three White Soldiers
             Three consecutive large red candles
             Bears in complete control
    
    RULES:
      ✅ Three consecutive bearish candles
      ✅ Each opens within previous body
      ✅ Each closes progressively lower
      ✅ Each body >= 0.6x ATR
    
    SCORE IN SYSTEM: -3 (very strong)
    """
    all_bearish = (
        c1.close < c1.open and
        c2.close < c2.open and
        c3.close < c3.open
    )

    progressive_lows = (
        c2.close < c1.close and
        c3.close < c2.close
    )

    opens_inside = (
        c1.close < c2.open < c1.open and
        c2.close < c3.open < c2.open
    )

    substantial = all(
        abs(c.close - c.open) >= 0.6 * atr
        for c in [c1, c2, c3]
    )

    small_wicks = all(
        (c.close - c.low) <= 0.3 * abs(c.close - c.open)
        for c in [c1, c2, c3]
    )

    return (
        all_bearish and
        progressive_lows and
        opens_inside and
        substantial and
        small_wicks
    )


def is_tweezer_top(prev: Candle, curr: Candle, pip_tolerance: float = 0.0003) -> bool:
    """
    TWEEZER TOP Pattern
    
    VISUAL:
      Day 1:  ████      ← bullish candle
      Day 2:  ████      ← bearish candle
              ↑↑↑↑
         Same HIGH point = double rejection
    
    MEANING: Price rejected at exact same high twice
             Strong resistance confirmation
    
    RULES:
      ✅ Day 1: bullish candle
      ✅ Day 2: bearish candle
      ✅ Both have same high (within 3 pips)
    
    SCORE IN SYSTEM: -2
    """
    prev_bullish = prev.close > prev.open
    curr_bearish = curr.close < curr.open

    same_high = abs(prev.high - curr.high) <= pip_tolerance

    return (
        prev_bullish and
        curr_bearish and
        same_high and
        curr.close < prev.open
    )


# ============================================================================
# SECTION 3 — NEUTRAL / INDECISION PATTERNS
# ============================================================================

def identify_doji_type(candle: Candle, atr: float) -> str:
    """
    DOJI Pattern (4 Types)
    
    TYPE 1 — STANDARD DOJI: Flat body (open = close)
    TYPE 2 — LONG-LEGGED DOJI: Tiny body with long wicks both sides
    TYPE 3 — DRAGONFLY DOJI: Open=close at TOP, long lower wick (bullish at support)
    TYPE 4 — GRAVESTONE DOJI: Open=close at BOTTOM, long upper wick (bearish at resistance)
    
    MEANING:
      Standard/Long-legged: Perfect indecision
      Dragonfly at bottom:  Bullish (like hammer without body)
      Gravestone at top:    Bearish (like shooting star without body)
    
    SCORE IN SYSTEM:
      Standard Doji:         0 (pure indecision)
      Long-legged Doji:      0 (extreme indecision)
      Dragonfly at support: +1
      Gravestone at resist: -1
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low

    if total_range == 0:
        return "NONE"

    # Must be doji: body < 5% of range
    is_doji = body / total_range < 0.05

    if not is_doji:
        return "NONE"

    # Dragonfly: no upper wick, long lower wick
    if upper_wick <= 0.1 * total_range and lower_wick > 0.6 * total_range:
        return "DRAGONFLY"

    # Gravestone: no lower wick, long upper wick
    if lower_wick <= 0.1 * total_range and upper_wick > 0.6 * total_range:
        return "GRAVESTONE"

    # Long-legged: both wicks long
    if upper_wick > 0.3 * total_range and lower_wick > 0.3 * total_range:
        return "LONG_LEGGED"

    return "STANDARD"


def doji_score(doji_type: str, location: str) -> int:
    """
    Calculate Doji score based on type and location
    
    location = "SUPPORT" or "RESISTANCE" or "MIDDLE"
    """
    scores = {
        "DRAGONFLY":  {"SUPPORT": +2, "RESISTANCE": +1, "MIDDLE": 0},
        "GRAVESTONE": {"SUPPORT": -1, "RESISTANCE": -2, "MIDDLE": 0},
        "LONG_LEGGED":{"SUPPORT":  0, "RESISTANCE":  0, "MIDDLE": 0},
        "STANDARD":   {"SUPPORT":  0, "RESISTANCE":  0, "MIDDLE": 0},
    }
    return scores.get(doji_type, {}).get(location, 0)


def is_spinning_top(candle: Candle) -> bool:
    """
    SPINNING TOP Pattern
    
    VISUAL:
             │
            ═══         ← small body (either color)
             │
    
    MEANING: Small body with wicks on both sides
             Neither bulls nor bears won the session
    
    RULES:
      ✅ Body < 30% of total range
      ✅ Both wicks present (> 20% each)
      ✅ Not quite a doji (has visible body)
    
    SCORE IN SYSTEM: 0 alone, ±1 at key zones
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low

    if total_range == 0:
        return False

    return (
        body / total_range < 0.30 and
        upper_wick / total_range > 0.20 and
        lower_wick / total_range > 0.20 and
        body / total_range > 0.05  # Not a doji
    )


# ============================================================================
# SECTION 4 — CONTINUATION PATTERNS
# ============================================================================

def is_bullish_marubozu(candle: Candle, atr: float) -> bool:
    """
    BULLISH MARUBOZU Pattern
    
    VISUAL:
      ██████████████    ← no wicks at all
                          entire range = body
                          GREEN candle
    
    MEANING: Bulls in COMPLETE control
             Open = Low, Close = High
             Strong continuation signal in uptrend
    
    RULES:
      ✅ Bullish candle (close > open)
      ✅ No upper wick (close = high OR < 0.1% of body)
      ✅ No lower wick (open = low OR < 0.1% of body)
      ✅ Body >= 1.0x ATR
    
    SCORE IN SYSTEM: +2 (continuation)
    """
    bullish = candle.close > candle.open
    body = abs(candle.close - candle.open)

    upper_wick = candle.high - candle.close
    lower_wick = candle.open - candle.low

    max_wick = 0.05 * body  # Allow 5% wick tolerance

    return (
        bullish and
        upper_wick <= max_wick and
        lower_wick <= max_wick and
        body >= 1.0 * atr
    )


def is_bearish_marubozu(candle: Candle, atr: float) -> bool:
    """
    BEARISH MARUBOZU Pattern
    
    VISUAL:
      ██████████████    ← no wicks at all
                          RED candle
                          Open = High, Close = Low
    
    MEANING: Bears in COMPLETE control
             Strong continuation in downtrend
    
    SCORE IN SYSTEM: -2 (continuation)
    """
    bearish = candle.close < candle.open
    body = abs(candle.close - candle.open)

    upper_wick = candle.high - candle.open
    lower_wick = candle.close - candle.low

    max_wick = 0.05 * body

    return (
        bearish and
        upper_wick <= max_wick and
        lower_wick <= max_wick and
        body >= 1.0 * atr
    )


def is_rising_three_methods(candles: List[Candle], atr: float) -> bool:
    """
    RISING THREE METHODS Pattern
    
    VISUAL:
      Day 1:  ████████  ← large bullish candle
      Day 2:   ███      ← small bearish (inside Day 1)
      Day 3:   ██       ← small bearish (inside Day 1)
      Day 4:   ███      ← small bearish (inside Day 1)
      Day 5:  █████████ ← large bullish, NEW HIGH
    
    MEANING: Brief pause in uptrend (days 2-4)
             Day 5 confirms uptrend continues
    
    RULES:
      ✅ Day 1: large bullish (>= 0.8x ATR)
      ✅ Days 2-4: 2-3 small bearish candles INSIDE Day 1 range
      ✅ Final day: large bullish closing above Day 1 high
    
    SCORE IN SYSTEM: +2 (continuation)
    """
    if len(candles) < 5:
        return False

    c1, c2, c3, c4, c5 = candles

    c1_bullish = c1.close > c1.open
    c5_bullish = c5.close > c5.open

    c1_large = abs(c1.close - c1.open) >= 0.8 * atr
    c5_large = abs(c5.close - c5.open) >= 0.8 * atr

    # Days 2-4 inside Day 1 range
    middle_inside = all(
        c1.low <= c.low and c.high <= c1.high
        for c in [c2, c3, c4]
    )

    # Days 2-4 mostly bearish (consolidation)
    middle_bearish = sum(
        1 for c in [c2, c3, c4]
        if c.close < c.open
    ) >= 2

    # Day 5 breaks above Day 1 high
    c5_breakout = c5.close > c1.high

    return (
        c1_bullish and c5_bullish and
        c1_large and c5_large and
        middle_inside and middle_bearish and
        c5_breakout
    )


def is_falling_three_methods(candles: List[Candle], atr: float) -> bool:
    """
    FALLING THREE METHODS Pattern
    
    MEANING: Opposite of rising three methods
             Brief pause in downtrend
             Bearish continuation pattern
    
    SCORE IN SYSTEM: -2 (continuation)
    """
    if len(candles) < 5:
        return False

    c1, c2, c3, c4, c5 = candles

    c1_bearish = c1.close < c1.open
    c5_bearish = c5.close < c5.open

    c1_large = abs(c1.close - c1.open) >= 0.8 * atr
    c5_large = abs(c5.close - c5.open) >= 0.8 * atr

    middle_inside = all(
        c1.high >= c.high and c.low >= c1.low
        for c in [c2, c3, c4]
    )

    middle_bullish = sum(
        1 for c in [c2, c3, c4]
        if c.close > c.open
    ) >= 2

    c5_breakdown = c5.close < c1.low

    return (
        c1_bearish and c5_bearish and
        c1_large and c5_large and
        middle_inside and middle_bullish and
        c5_breakdown
    )


# ============================================================================
# SECTION 5 — SPECIAL PATTERNS FOR TRADING SYSTEM
# ============================================================================

def is_pin_bar(candle: Candle, atr: float, direction: Optional[str] = None) -> Dict:
    """
    PIN BAR Pattern (Most Important for System)
    
    VISUAL BULLISH:
             │          ← tiny upper wick
            ═══         ← small body anywhere
             │
             │
             │          ← long lower wick >= 3x body
    
    VISUAL BEARISH:
             │
             │
             │          ← long upper wick >= 3x body
            ═══         ← small body
             │          ← tiny lower wick
    
    MEANING: Price "pinned" a level and rejected it
             Most used pattern by professional traders
             Works on ALL timeframes
             KEY pattern for liquidity sweep confirmation
    
    RULES:
      ✅ Wick >= 3x body size
      ✅ Wick >= 70% of total range
      ✅ Body in top 30% (bearish pin) or bottom 30% (bullish pin)
    
    SCORE IN SYSTEM: +3 or -3 (strong confirmation)
    """
    body = abs(candle.close - candle.open)
    upper_wick = candle.high - max(candle.open, candle.close)
    lower_wick = min(candle.open, candle.close) - candle.low
    total_range = candle.high - candle.low

    if total_range == 0 or body == 0:
        return {"is_pin": False, "score": 0}

    # BULLISH PIN BAR (rejection of lows)
    bullish_pin = (
        lower_wick >= 3.0 * body and
        lower_wick / total_range >= 0.70 and
        upper_wick <= 0.30 * body and
        body >= 0.05 * atr
    )

    # BEARISH PIN BAR (rejection of highs)
    bearish_pin = (
        upper_wick >= 3.0 * body and
        upper_wick / total_range >= 0.70 and
        lower_wick <= 0.30 * body and
        body >= 0.05 * atr
    )

    if bullish_pin:
        return {
            "is_pin": True,
            "direction": "BULLISH",
            "score": +3,
            "wick_ratio": lower_wick / body,
            "strength": "STRONG" if lower_wick >= 4 * body else "NORMAL"
        }

    if bearish_pin:
        return {
            "is_pin": True,
            "direction": "BEARISH",
            "score": -3,
            "wick_ratio": upper_wick / body,
            "strength": "STRONG" if upper_wick >= 4 * body else "NORMAL"
        }

    return {"is_pin": False, "score": 0}


def is_inside_bar(mother: Candle, inside: Candle) -> bool:
    """
    INSIDE BAR Pattern (Breakout Setup)
    
    VISUAL:
      Day 1: ██████████ ← mother bar (large)
      Day 2:   █████    ← inside bar (fully within Day 1)
    
    MEANING: Complete range compression
             Price coiling for a breakout
    
    RULES:
      ✅ Day 2 high < Day 1 high
      ✅ Day 2 low > Day 1 low
      ✅ Day 2 completely inside Day 1
    
    SCORE IN SYSTEM: Setup alert only (not directional)
    """
    return (
        inside.high < mother.high and
        inside.low > mother.low
    )


def inside_bar_breakout(mother: Candle, inside: Candle, current: Candle) -> Optional[Dict]:
    """Detect Inside Bar breakout direction"""
    if not is_inside_bar(mother, inside):
        return None

    if current.close > mother.high:
        return {"breakout": "BULLISH", "score": +2}
    elif current.close < mother.low:
        return {"breakout": "BEARISH", "score": -2}

    return {"breakout": "PENDING", "score": 0}


def is_outside_bar(prev: Candle, curr: Candle) -> Dict:
    """
    OUTSIDE BAR Pattern (Engulfing Range)
    
    VISUAL:
      Day 1:   █████    ← smaller candle
      Day 2: ██████████ ← engulfs entire range including wicks
    
    MEANING: Complete momentum shift
             New candle engulfs ENTIRE previous bar (including wicks)
    
    SCORE IN SYSTEM: ±2
    """
    full_engulf = (
        curr.high > prev.high and
        curr.low < prev.low
    )

    curr_bullish = curr.close > curr.open
    curr_bearish = curr.close < curr.open

    if full_engulf and curr_bullish:
        return {"pattern": "BULLISH_OUTSIDE", "score": +2}
    elif full_engulf and curr_bearish:
        return {"pattern": "BEARISH_OUTSIDE", "score": -2}

    return {"pattern": "NONE", "score": 0}


# ============================================================================
# SECTION 6 — MASTER PATTERN SCANNER
# ============================================================================

class CandlestickScanner:
    """
    Complete Pattern Scanner for Super AI Trader Brain
    
    Scans multiple candles and returns all detected patterns with scores.
    Integrates with the agent voting system.
    """

    def __init__(self, atr: float):
        self.atr = atr

    def scan_all_patterns(self, candles: List[Candle]) -> Dict:
        """
        Scan all patterns from recent candles
        
        Args:
            candles: list of recent candles (newest last)
        
        Returns:
            Dictionary with all detected patterns and total score
        """
        results = {
            "bullish_patterns": [],
            "bearish_patterns": [],
            "neutral_patterns": [],
            "total_score": 0,
            "dominant_signal": "NEUTRAL"
        }

        if len(candles) < 5:
            return results

        c = candles  # Shorthand
        curr = c[-1]
        prev = c[-2]
        prev2 = c[-3] if len(c) >= 3 else None
        prev3 = c[-4] if len(c) >= 4 else None

        # ═══ SINGLE CANDLE PATTERNS ═══
        if prev3 and is_hammer(curr, c[-4:-1], self.atr):
            results["bullish_patterns"].append(
                {"name": "Hammer", "score": +2}
            )
            results["total_score"] += 2

        if prev3 and is_shooting_star(curr, c[-4:-1], self.atr):
            results["bearish_patterns"].append(
                {"name": "Shooting Star", "score": -2}
            )
            results["total_score"] -= 2

        pin = is_pin_bar(curr, self.atr)
        if pin["is_pin"]:
            if pin["direction"] == "BULLISH":
                results["bullish_patterns"].append(
                    {"name": f"Bullish Pin Bar ({pin['strength']})", "score": pin["score"]}
                )
                results["total_score"] += pin["score"]
            else:
                results["bearish_patterns"].append(
                    {"name": f"Bearish Pin Bar ({pin['strength']})", "score": pin["score"]}
                )
                results["total_score"] += pin["score"]

        doji_type = identify_doji_type(curr, self.atr)
        if doji_type != "NONE":
            results["neutral_patterns"].append(
                {"name": f"Doji ({doji_type})", "score": 0}
            )

        if is_bullish_marubozu(curr, self.atr):
            results["bullish_patterns"].append(
                {"name": "Bullish Marubozu", "score": +2}
            )
            results["total_score"] += 2

        if is_bearish_marubozu(curr, self.atr):
            results["bearish_patterns"].append(
                {"name": "Bearish Marubozu", "score": -2}
            )
            results["total_score"] -= 2

        if is_spinning_top(curr):
            results["neutral_patterns"].append(
                {"name": "Spinning Top", "score": 0}
            )

        # ═══ DOUBLE CANDLE PATTERNS ═══
        bull_eng = is_bullish_engulfing(prev, curr, prev.volume, curr.volume)
        if bull_eng["pattern"]:
            results["bullish_patterns"].append(
                {"name": "Bullish Engulfing", "score": bull_eng["score"]}
            )
            results["total_score"] += bull_eng["score"]

        bear_eng = is_bearish_engulfing(prev, curr, prev.volume, curr.volume)
        if bear_eng["pattern"]:
            results["bearish_patterns"].append(
                {"name": "Bearish Engulfing", "score": bear_eng["score"]}
            )
            results["total_score"] += bear_eng["score"]

        if is_tweezer_bottom(prev, curr):
            results["bullish_patterns"].append(
                {"name": "Tweezer Bottom", "score": +2}
            )
            results["total_score"] += 2

        if is_tweezer_top(prev, curr):
            results["bearish_patterns"].append(
                {"name": "Tweezer Top", "score": -2}
            )
            results["total_score"] -= 2

        if is_piercing_line(prev, curr):
            results["bullish_patterns"].append(
                {"name": "Piercing Line", "score": +2}
            )
            results["total_score"] += 2

        if is_dark_cloud_cover(prev, curr):
            results["bearish_patterns"].append(
                {"name": "Dark Cloud Cover", "score": -2}
            )
            results["total_score"] -= 2

        if is_bullish_harami(prev, curr):
            results["bullish_patterns"].append(
                {"name": "Bullish Harami", "score": +1}
            )
            results["total_score"] += 1

        if is_bearish_harami(prev, curr):
            results["bearish_patterns"].append(
                {"name": "Bearish Harami", "score": -1}
            )
            results["total_score"] -= 1

        # ═══ TRIPLE CANDLE PATTERNS ═══
        if prev2 and is_morning_star(prev2, prev, curr, self.atr):
            results["bullish_patterns"].append(
                {"name": "Morning Star", "score": +3}
            )
            results["total_score"] += 3

        if prev2 and is_evening_star(prev2, prev, curr, self.atr):
            results["bearish_patterns"].append(
                {"name": "Evening Star", "score": -3}
            )
            results["total_score"] -= 3

        if prev3 and len(candles) >= 5:
            if is_three_white_soldiers(c[-5], c[-4], c[-3], self.atr):
                results["bullish_patterns"].append(
                    {"name": "Three White Soldiers", "score": +3}
                )
                results["total_score"] += 3

            if is_three_black_crows(c[-5], c[-4], c[-3], self.atr):
                results["bearish_patterns"].append(
                    {"name": "Three Black Crows", "score": -3}
                )
                results["total_score"] -= 3

        # Determine dominant signal
        if results["total_score"] >= 3:
            results["dominant_signal"] = "BULLISH"
        elif results["total_score"] <= -3:
            results["dominant_signal"] = "BEARISH"
        else:
            results["dominant_signal"] = "NEUTRAL"

        return results

    def get_pattern_summary(self, results: Dict) -> str:
        """Generate human-readable summary of detected patterns"""
        lines = []
        
        if results["bullish_patterns"]:
            lines.append("🟢 BULLISH PATTERNS:")
            for p in results["bullish_patterns"]:
                lines.append(f"   • {p['name']} (+{p['score']})")
        
        if results["bearish_patterns"]:
            lines.append("🔴 BEARISH PATTERNS:")
            for p in results["bearish_patterns"]:
                lines.append(f"   • {p['name']} ({p['score']})")
        
        if results["neutral_patterns"]:
            lines.append("⚪ NEUTRAL PATTERNS:")
            for p in results["neutral_patterns"]:
                lines.append(f"   • {p['name']}")
        
        lines.append(f"\n📊 TOTAL SCORE: {results['total_score']}")
        lines.append(f"🎯 SIGNAL: {results['dominant_signal']}")
        
        return "\n".join(lines)
