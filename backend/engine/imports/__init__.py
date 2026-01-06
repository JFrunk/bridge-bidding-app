"""
ACBL Tournament Import Module

Supports multiple import formats:
1. PBN files - Hand records with optional DDS analysis
2. BWS files - Contract results from ACBLscore/BridgeMate

Three-stage pipeline for analysis:
1. Parser - Extracts deals, auctions, results from source files
2. Logic Mapper - Converts to V3 API format for enhanced_extractor
3. Feature Injection - Calculates panic_index, working_hcp_ratio for analysis

To register API endpoints in server.py:
    from engine.imports import register_acbl_import_endpoints
    register_acbl_import_endpoints(app)
"""

from .pbn_importer import (
    parse_pbn_file,
    parse_pbn_hand,
    extract_acbl_auction,
    convert_pbn_deal_to_json,
    PBNHand,
    PBNFile
)

from .bws_importer import (
    parse_bws_file,
    parse_bws_contracts,
    merge_bws_with_pbn,
    BWSFile,
    BWSContract,
    BWSHandRecord,
    BWSBid
)

from .acbl_audit_service import (
    generate_audit_report,
    AuditResult,
    compare_tournament_vs_engine
)

from .acbl_import_api import register_acbl_import_endpoints

__all__ = [
    # PBN Parser
    'parse_pbn_file',
    'parse_pbn_hand',
    'extract_acbl_auction',
    'convert_pbn_deal_to_json',
    'PBNHand',
    'PBNFile',
    # BWS Parser
    'parse_bws_file',
    'parse_bws_contracts',
    'merge_bws_with_pbn',
    'BWSFile',
    'BWSContract',
    'BWSHandRecord',
    'BWSBid',
    # Audit service
    'generate_audit_report',
    'AuditResult',
    'compare_tournament_vs_engine',
    # API registration
    'register_acbl_import_endpoints'
]
