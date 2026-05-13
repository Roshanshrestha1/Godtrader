"""
Configuration loader for the Stable Stock Analysis System.
Loads settings from config.yaml and provides easy access to all parameters.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class Config:
    """Singleton configuration class that loads and manages all system settings."""
    
    _instance = None
    _config_data = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from config.yaml file."""
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            self._config_data = yaml.safe_load(f)
        
        # Override with environment variables if available
        self._load_env_overrides()
    
    def _load_env_overrides(self) -> None:
        """Override config values with environment variables."""
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            if 'telegram' not in self._config_data:
                self._config_data['telegram'] = {}
            self._config_data['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if os.getenv('ADX_THRESHOLD'):
            self._config_data['analysis']['adx_threshold'] = int(os.getenv('ADX_THRESHOLD'))
        
        if os.getenv('MIN_CONFIDENCE'):
            self._config_data['master_brain']['min_confidence'] = int(os.getenv('MIN_CONFIDENCE'))
    
    @property
    def analysis(self) -> Dict[str, Any]:
        """Analysis parameters."""
        return self._config_data.get('analysis', {})
    
    @property
    def risk(self) -> Dict[str, Any]:
        """Risk management parameters."""
        return self._config_data.get('risk', {})
    
    @property
    def data(self) -> Dict[str, Any]:
        """Data fetching parameters."""
        return self._config_data.get('data', {})
    
    @property
    def output(self) -> Dict[str, Any]:
        """Output/logging parameters."""
        return self._config_data.get('output', {})
    
    @property
    def telegram(self) -> Dict[str, Any]:
        """Telegram bot parameters."""
        return self._config_data.get('telegram', {})
    
    @property
    def symbols(self) -> Dict[str, List[str]]:
        """Symbol groups."""
        return self._config_data.get('symbols', {})
    
    @property
    def supported_timeframes(self) -> List[str]:
        """List of supported timeframes."""
        return self._config_data.get('supported_timeframes', [])
    
    @property
    def master_brain(self) -> Dict[str, Any]:
        """Master Brain thresholds."""
        return self._config_data.get('master_brain', {})
    
    # Convenience methods
    def get_adx_threshold(self) -> int:
        return self.analysis.get('adx_threshold', 25)
    
    def get_ema_period(self) -> int:
        return self.analysis.get('ema_period', 200)
    
    def get_volume_sma_period(self) -> int:
        return self.analysis.get('volume_sma_period', 20)
    
    def get_sweep_lookback_hours(self) -> int:
        return self.analysis.get('sweep_lookback_hours', 24)
    
    def get_main_timeframe(self) -> str:
        return self.analysis.get('main_timeframe', '1h')
    
    def get_entry_timeframe(self) -> str:
        return self.analysis.get('entry_timeframe', '5m')
    
    def get_stop_atr_multiplier(self) -> float:
        return self.risk.get('default_stop_atr_multiplier', 1.5)
    
    def get_target_atr_multiplier(self) -> float:
        return self.risk.get('default_target_atr_multiplier', 3.0)
    
    def get_max_staleness_seconds(self) -> int:
        return self.data.get('max_staleness_seconds', 120)
    
    def get_retry_attempts(self) -> int:
        return self.data.get('retry_attempts', 3)
    
    def get_retry_backoff_base(self) -> float:
        return self.data.get('retry_backoff_base', 1.0)
    
    def get_log_file(self) -> str:
        return self.output.get('log_file', 'signals.log')
    
    def is_verbose(self) -> bool:
        return self.output.get('verbose', True)
    
    def get_bot_token(self) -> Optional[str]:
        return self.telegram.get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
    
    def get_admin_user_ids(self) -> List[int]:
        return self.telegram.get('admin_user_ids', [])
    
    def get_min_agents_agree(self) -> int:
        return self.master_brain.get('min_agents_agree', 4)
    
    def get_min_confidence(self) -> int:
        return self.master_brain.get('min_confidence', 65)
    
    def is_agent5_veto_enabled(self) -> bool:
        return self.master_brain.get('agent5_veto_enabled', True)
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols from all groups."""
        all_symbols = []
        for group_symbols in self.symbols.values():
            all_symbols.extend(group_symbols)
        return all_symbols
    
    def get_symbol_groups(self) -> Dict[str, str]:
        """Get mapping of symbol to group name."""
        symbol_groups = {}
        for group_name, symbols in self.symbols.items():
            for symbol in symbols:
                symbol_groups[symbol] = group_name
        return symbol_groups
    
    def get_symbol_mapping(self) -> Dict[str, str]:
        """Get mapping of Exness symbol names to Yahoo Finance tickers."""
        return self._config_data.get('symbol_mapping', {})
    
    def get_yahoo_ticker(self, symbol: str) -> str:
        """Get the Yahoo Finance ticker for a given Exness symbol."""
        mapping = self.get_symbol_mapping()
        return mapping.get(symbol, symbol)  # Return original if no mapping found
    
    def get_group_display_name(self, group_key: str) -> str:
        """Get a human-readable display name for a symbol group."""
        display_names = {
            'forex_majors': '💱 Forex Majors',
            'forex_minors_exotics': '🌍 Forex Minors & Exotics',
            'crypto': '₿ Cryptocurrencies',
            'metals': '🥇 Precious Metals',
            'energies': '🛢️ Energies',
            'indices': '📈 Major Indices',
            'stocks_us': '🏢 US Stocks'
        }
        return display_names.get(group_key, group_key.replace('_', ' ').title())


# Global config instance
config = Config()
