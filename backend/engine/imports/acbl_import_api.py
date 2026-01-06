"""
ACBL Import API - REST endpoints for PBN and BWS file import and tournament analysis.

Provides:
- PBN file upload and parsing (hand records with DDS)
- BWS file upload and parsing (contract results from ACBLscore)
- Tournament listing and details
- Hand-level analysis with V3 engine comparison
- Import status tracking
- Audit summary generation

To add to server.py:
    from engine.imports.acbl_import_api import register_acbl_import_endpoints
    register_acbl_import_endpoints(app)
"""

import json
import hashlib
import logging
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import request, jsonify, Flask
import sys
from pathlib import Path

# Database abstraction layer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db import get_connection

# Import the PBN parsing and audit modules
from .pbn_importer import (
    parse_pbn_file,
    parse_pbn_hand,
    PBNFile,
    PBNHand,
    convert_pbn_deal_to_json
)
from .bws_importer import (
    parse_bws_file,
    check_mdbtools_available,
    BWSFile,
    BWSContract
)
from .acbl_audit_service import (
    generate_audit_report,
    compare_tournament_vs_engine,
    analyze_pbn_hand_with_v3,
    AuditResult,
    TournamentAuditSummary
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def ensure_acbl_tables_exist():
    """Ensure the ACBL import tables exist in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='imported_tournaments'
    """)

    if not cursor.fetchone():
        # Read and execute migration
        migration_path = Path(__file__).parent.parent.parent / 'migrations' / '014_add_acbl_import_tables.sql'
        if migration_path.exists():
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
            # Execute each statement separately
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"Migration statement skipped: {e}")
            conn.commit()
            logger.info("Created ACBL import tables")
        else:
            logger.error(f"Migration file not found: {migration_path}")

    cursor.close()
    conn.close()


def get_content_hash(content: str) -> str:
    """Generate SHA256 hash of content for deduplication."""
    return hashlib.sha256(content.encode()).hexdigest()


# =============================================================================
# API ENDPOINT REGISTRATION
# =============================================================================

def register_acbl_import_endpoints(app: Flask):
    """Register all ACBL import API endpoints."""

    # Ensure tables exist on startup
    ensure_acbl_tables_exist()

    # =========================================================================
    # POST /api/import/pbn - Upload and parse a PBN file
    # =========================================================================
    @app.route('/api/import/pbn', methods=['POST'])
    def import_pbn_file():
        """
        Upload and parse a PBN file for tournament import.

        Request body (JSON):
        {
            "user_id": 1,
            "pbn_content": "...",  // Raw PBN file content
            "filename": "tournament.pbn"  // Optional filename
        }

        OR multipart/form-data:
        - file: PBN file
        - user_id: User ID

        Returns:
        {
            "tournament_id": 123,
            "event_name": "...",
            "total_hands": 24,
            "valid_hands": 24,
            "status": "processing"
        }
        """
        try:
            # Handle both JSON and file upload
            if request.content_type and 'multipart/form-data' in request.content_type:
                # File upload
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400

                file = request.files['file']
                pbn_content = file.read().decode('utf-8')
                filename = file.filename or 'upload.pbn'
                user_id = request.form.get('user_id', 0)
            else:
                # JSON body
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400

                pbn_content = data.get('pbn_content', '')
                filename = data.get('filename', 'upload.pbn')
                user_id = data.get('user_id', 0)

            if not pbn_content:
                return jsonify({'error': 'Empty PBN content'}), 400

            # Check for duplicate import
            content_hash = get_content_hash(pbn_content)
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, event_name FROM imported_tournaments
                WHERE user_id = ? AND source_content_hash = ?
            """, (user_id, content_hash))

            existing = cursor.fetchone()
            if existing:
                cursor.close()
                conn.close()
                return jsonify({
                    'error': 'Duplicate import',
                    'message': f'This file was already imported as tournament ID {existing[0]}',
                    'tournament_id': existing[0],
                    'event_name': existing[1]
                }), 409

            # Parse the PBN file
            pbn_file = parse_pbn_file(pbn_content, filename)

            if pbn_file.valid_hands == 0:
                cursor.close()
                conn.close()
                return jsonify({
                    'error': 'No valid hands found',
                    'parsing_errors': pbn_file.parsing_errors
                }), 400

            # Create tournament record
            cursor.execute("""
                INSERT INTO imported_tournaments (
                    user_id, event_name, event_date, event_site,
                    scoring_method, source, source_filename, source_content_hash,
                    import_status, total_hands, hands_analyzed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                pbn_file.event_name or 'Imported Tournament',
                pbn_file.event_date,
                pbn_file.event_site,
                pbn_file.scoring_method,
                pbn_file.source,
                filename,
                content_hash,
                'processing',
                len(pbn_file.hands),
                0
            ))

            tournament_id = cursor.lastrowid

            # Insert individual hands
            hands_inserted = 0
            for hand in pbn_file.hands:
                if not hand.is_valid:
                    continue

                # Convert auction to JSON
                auction_json = json.dumps(hand.auction_history)

                # Get deal JSON for quick access
                deal_json = json.dumps({
                    'N': convert_pbn_deal_to_json(hand.hands.get('N', '')),
                    'E': convert_pbn_deal_to_json(hand.hands.get('E', '')),
                    'S': convert_pbn_deal_to_json(hand.hands.get('S', '')),
                    'W': convert_pbn_deal_to_json(hand.hands.get('W', ''))
                })

                cursor.execute("""
                    INSERT INTO imported_hands (
                        tournament_id, user_id, board_number,
                        dealer, vulnerability, deal_pbn, deal_json,
                        hand_north, hand_east, hand_south, hand_west,
                        auction_history, auction_raw,
                        contract_level, contract_strain, contract_doubled,
                        contract_declarer, tricks_taken,
                        score_ns, score_ew,
                        analysis_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tournament_id,
                    user_id,
                    hand.board_number,
                    hand.dealer,
                    hand.vulnerability,
                    f"{hand.dealer}:{' '.join(hand.hands.get(p, '') for p in ['N', 'E', 'S', 'W'])}",
                    deal_json,
                    hand.hands.get('N', ''),
                    hand.hands.get('E', ''),
                    hand.hands.get('S', ''),
                    hand.hands.get('W', ''),
                    auction_json,
                    hand.auction_raw,
                    hand.contract_level,
                    hand.contract_strain,
                    hand.contract_doubled,
                    hand.contract_declarer,
                    hand.tricks_taken,
                    hand.score_ns,
                    hand.score_ew,
                    'pending'
                ))
                hands_inserted += 1

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'tournament_id': tournament_id,
                'event_name': pbn_file.event_name,
                'event_date': pbn_file.event_date,
                'source': pbn_file.source,
                'total_hands': len(pbn_file.hands),
                'valid_hands': hands_inserted,
                'invalid_hands': len(pbn_file.hands) - hands_inserted,
                'parsing_errors': pbn_file.parsing_errors[:5],  # First 5 errors
                'status': 'processing'
            })

        except Exception as e:
            logger.exception(f"Error importing PBN file: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # POST /api/import/bws - Upload and parse a BWS file
    # =========================================================================
    @app.route('/api/import/bws', methods=['POST'])
    def import_bws_file():
        """
        Upload and parse a BWS file for contract results import.

        BWS files are Microsoft Access databases from ACBLscore containing:
        - ReceivedData: Contract results (declarer, contract, result)
        - HandRecord: Deal distributions (if populated)
        - BiddingData: Individual bids (if captured by BridgeMate)

        Requires: mdbtools (brew install mdbtools on macOS)

        Request: multipart/form-data with 'file' field

        Returns:
        {
            "filename": "...",
            "board_count": 24,
            "table_count": 12,
            "contracts": [...],
            "has_hand_records": false,
            "has_bidding_data": false,
            "tables_available": [...]
        }
        """
        try:
            # Check mdbtools availability
            available, error = check_mdbtools_available()
            if not available:
                return jsonify({
                    'error': 'BWS parsing not available',
                    'message': error,
                    'install_hint': 'brew install mdbtools'
                }), 501

            # Handle file upload
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400

            file = request.files['file']
            if not file.filename:
                return jsonify({'error': 'No filename'}), 400

            # BWS files are binary Access databases, write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bws') as tmp:
                file.save(tmp.name)
                temp_path = tmp.name

            try:
                # Parse the BWS file
                bws = parse_bws_file(temp_path)

                # Return parsed data
                return jsonify({
                    'filename': file.filename,
                    'board_count': bws.board_count,
                    'table_count': bws.table_count,
                    'contract_count': len(bws.contracts),
                    'has_hand_records': bws.has_hand_records,
                    'has_bidding_data': bws.has_bidding_data,
                    'tables_available': bws.tables_available,
                    'contracts': [c.to_dict() for c in bws.contracts[:100]],  # First 100
                    'sample_by_board': _get_sample_by_board(bws)
                })

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.exception(f"Error importing BWS file: {e}")
            return jsonify({'error': str(e)}), 500

    def _get_sample_by_board(bws: BWSFile) -> Dict[int, List[Dict]]:
        """Get sample contracts organized by board number."""
        sample = {}
        for board_num in sorted(set(c.board for c in bws.contracts))[:24]:
            contracts = bws.get_contracts_for_board(board_num)
            sample[board_num] = [c.to_dict() for c in contracts[:3]]  # First 3 per board
        return sample

    # =========================================================================
    # POST /api/import/merge - Merge PBN and BWS data
    # =========================================================================
    @app.route('/api/import/merge', methods=['POST'])
    def merge_pbn_bws():
        """
        Merge PBN hand records with BWS contract results and save to database.

        Request: multipart/form-data with:
        - pbn_file: PBN file with hand records
        - bws_file: BWS file with contract results
        - user_id: User ID

        Returns merged tournament data with tournament_id for tracking.
        """
        try:
            # Check mdbtools for BWS
            available, error = check_mdbtools_available()
            if not available:
                return jsonify({'error': error, 'install_hint': 'brew install mdbtools'}), 501

            if 'pbn_file' not in request.files or 'bws_file' not in request.files:
                return jsonify({'error': 'Both pbn_file and bws_file are required'}), 400

            pbn_file = request.files['pbn_file']
            bws_file = request.files['bws_file']
            user_id = request.form.get('user_id', 0, type=int)

            # Parse PBN
            pbn_content = pbn_file.read().decode('utf-8')
            pbn = parse_pbn_file(pbn_content, pbn_file.filename)

            # Parse BWS (write to temp file)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bws') as tmp:
                bws_file.save(tmp.name)
                temp_path = tmp.name

            try:
                bws = parse_bws_file(temp_path)

                # Create tournament record in database
                conn = get_connection()
                cursor = conn.cursor()

                content_hash = get_content_hash(pbn_content + bws_file.filename)

                cursor.execute("""
                    INSERT INTO imported_tournaments (
                        user_id, event_name, event_date, event_site,
                        scoring_method, source, source_filename, source_content_hash,
                        import_status, total_hands, hands_analyzed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    pbn.event_name or 'Merged Tournament',
                    pbn.event_date,
                    pbn.event_site,
                    pbn.scoring_method,
                    f"{pbn.source}+bws",  # Indicate merged source
                    f"{pbn_file.filename} + {bws_file.filename}",
                    content_hash,
                    'processing',
                    len(pbn.hands),
                    0
                ))

                tournament_id = cursor.lastrowid

                # Insert hands with contract data
                hands_inserted = 0
                for hand in pbn.hands:
                    if not hand.is_valid:
                        continue

                    board_num = hand.board_number
                    contracts = bws.get_contracts_for_board(board_num)

                    # Store contract results as JSON
                    contracts_json = json.dumps([c.to_dict() for c in contracts])

                    # Get DDS data
                    dds_json = json.dumps(hand.dds_tricks) if hand.dds_tricks else None

                    # Build deal JSON
                    deal_json = json.dumps({
                        'N': convert_pbn_deal_to_json(hand.hands.get('N', '')),
                        'E': convert_pbn_deal_to_json(hand.hands.get('E', '')),
                        'S': convert_pbn_deal_to_json(hand.hands.get('S', '')),
                        'W': convert_pbn_deal_to_json(hand.hands.get('W', ''))
                    })

                    cursor.execute("""
                        INSERT INTO imported_hands (
                            tournament_id, user_id, board_number,
                            dealer, vulnerability, deal_pbn, deal_json,
                            hand_north, hand_east, hand_south, hand_west,
                            auction_history, auction_raw,
                            contract_level, contract_strain, contract_doubled,
                            contract_declarer, tricks_taken,
                            score_ns, score_ew,
                            dds_analysis, optimum_score, par_contract,
                            tournament_contracts,
                            analysis_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tournament_id,
                        user_id,
                        board_num,
                        hand.dealer,
                        hand.vulnerability,
                        f"{hand.dealer}:{' '.join(hand.hands.get(p, '') for p in ['N', 'E', 'S', 'W'])}",
                        deal_json,
                        hand.hands.get('N', ''),
                        hand.hands.get('E', ''),
                        hand.hands.get('S', ''),
                        hand.hands.get('W', ''),
                        json.dumps(hand.auction_history) if hand.auction_history else '[]',
                        hand.auction_raw,
                        hand.contract_level,
                        hand.contract_strain,
                        hand.contract_doubled,
                        hand.contract_declarer,
                        hand.tricks_taken,
                        hand.score_ns,
                        hand.score_ew,
                        dds_json,
                        hand.optimum_score,
                        hand.par_contract,
                        contracts_json,  # Store BWS contract results
                        'pending'
                    ))
                    hands_inserted += 1

                conn.commit()
                cursor.close()
                conn.close()

                return jsonify({
                    'success': True,
                    'tournament_id': tournament_id,
                    'pbn_filename': pbn_file.filename,
                    'bws_filename': bws_file.filename,
                    'boards_in_pbn': len(pbn.hands),
                    'boards_in_bws': bws.board_count,
                    'boards_merged': hands_inserted,
                    'total_contracts': len(bws.contracts),
                    'has_dds_data': any(h.dds_tricks for h in pbn.hands),
                    'has_bidding_data': bws.has_bidding_data,
                    'status': 'processing'
                })

            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.exception(f"Error merging PBN/BWS files: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # GET /api/tournaments - List imported tournaments
    # =========================================================================
    @app.route('/api/tournaments', methods=['GET'])
    def list_tournaments():
        """
        List imported tournaments for a user.

        Query params:
        - user_id: Required user ID
        - status: Optional filter by import_status
        - limit: Max results (default 50)
        - offset: Pagination offset

        Returns:
        {
            "tournaments": [...],
            "total": 10,
            "has_more": false
        }
        """
        try:
            user_id = request.args.get('user_id', type=int)
            status = request.args.get('status')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)

            if not user_id:
                return jsonify({'error': 'user_id is required'}), 400

            conn = get_connection()
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT id, event_name, event_date, event_site, scoring_method,
                       source, import_status, total_hands, hands_analyzed,
                       alignment_rate, total_potential_savings, imported_at
                FROM imported_tournaments
                WHERE user_id = ?
            """
            params = [user_id]

            if status:
                query += " AND import_status = ?"
                params.append(status)

            query += " ORDER BY imported_at DESC LIMIT ? OFFSET ?"
            params.extend([limit + 1, offset])  # +1 to check has_more

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            columns = ['id', 'event_name', 'event_date', 'event_site', 'scoring_method',
                       'source', 'import_status', 'total_hands', 'hands_analyzed',
                       'alignment_rate', 'total_potential_savings', 'imported_at']

            tournaments = []
            for row in rows[:limit]:
                tournaments.append(dict(zip(columns, row)))

            # Get total count
            cursor.execute("""
                SELECT COUNT(*) FROM imported_tournaments WHERE user_id = ?
            """, (user_id,))
            total = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return jsonify({
                'tournaments': tournaments,
                'total': total,
                'has_more': len(rows) > limit
            })

        except Exception as e:
            logger.exception(f"Error listing tournaments: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # GET /api/tournaments/<id> - Get tournament details
    # =========================================================================
    @app.route('/api/tournaments/<int:tournament_id>', methods=['GET'])
    def get_tournament_detail(tournament_id: int):
        """
        Get detailed tournament information with aggregate statistics.

        Returns tournament metadata, summary statistics, and audit breakdown.
        """
        try:
            user_id = request.args.get('user_id', type=int)

            conn = get_connection()
            cursor = conn.cursor()

            # Get tournament
            cursor.execute("""
                SELECT * FROM imported_tournaments WHERE id = ?
            """, (tournament_id,))

            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Tournament not found'}), 404

            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            tournament = dict(zip(columns, row))

            # Verify user access
            if user_id and tournament['user_id'] != user_id:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Access denied'}), 403

            # Get audit category breakdown
            cursor.execute("""
                SELECT audit_category, COUNT(*) as count
                FROM imported_hands
                WHERE tournament_id = ?
                GROUP BY audit_category
            """, (tournament_id,))

            category_breakdown = {}
            for cat_row in cursor.fetchall():
                category_breakdown[cat_row[0] or 'pending'] = cat_row[1]

            # Get quadrant breakdown
            cursor.execute("""
                SELECT quadrant, COUNT(*) as count
                FROM imported_hands
                WHERE tournament_id = ? AND quadrant IS NOT NULL
                GROUP BY quadrant
            """, (tournament_id,))

            quadrant_breakdown = {}
            for quad_row in cursor.fetchall():
                quadrant_breakdown[quad_row[0]] = quad_row[1]

            # Get hands flagged for review (falsified)
            cursor.execute("""
                SELECT board_number FROM imported_hands
                WHERE tournament_id = ? AND is_falsified = 1
                ORDER BY board_number
            """, (tournament_id,))

            flagged_boards = [r[0] for r in cursor.fetchall()]

            cursor.close()
            conn.close()

            tournament['category_breakdown'] = category_breakdown
            tournament['quadrant_breakdown'] = quadrant_breakdown
            tournament['flagged_for_review'] = flagged_boards

            return jsonify(tournament)

        except Exception as e:
            logger.exception(f"Error getting tournament detail: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # GET /api/tournaments/<id>/hands - List hands in tournament
    # =========================================================================
    @app.route('/api/tournaments/<int:tournament_id>/hands', methods=['GET'])
    def get_tournament_hands(tournament_id: int):
        """
        List hands in a tournament with analysis results.

        Query params:
        - user_id: Required
        - audit_category: Filter by category
        - quadrant: Filter by quadrant
        - is_falsified: Filter by falsification status
        - limit: Max results (default 50)
        - offset: Pagination offset
        - sort_by: Sort field (default: board_number)
        - sort_order: asc or desc
        """
        try:
            user_id = request.args.get('user_id', type=int)
            audit_category = request.args.get('audit_category')
            quadrant = request.args.get('quadrant')
            is_falsified = request.args.get('is_falsified', type=int)
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            sort_by = request.args.get('sort_by', 'board_number')
            sort_order = request.args.get('sort_order', 'asc')

            # Whitelist sort columns
            allowed_sort = ['board_number', 'score_delta', 'panic_index', 'audit_category']
            if sort_by not in allowed_sort:
                sort_by = 'board_number'

            conn = get_connection()
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT id, board_number, dealer, vulnerability,
                       hand_south, auction_history,
                       contract_level, contract_strain, contract_doubled,
                       tricks_taken, score_ns,
                       optimal_bid, theoretical_score,
                       panic_index, survival_status,
                       is_logic_aligned, is_falsified, score_delta,
                       bidding_efficiency, audit_category, educational_feedback,
                       quadrant, analysis_status, tournament_contracts
                FROM imported_hands
                WHERE tournament_id = ?
            """
            params = [tournament_id]

            if audit_category:
                query += " AND audit_category = ?"
                params.append(audit_category)

            if quadrant:
                query += " AND quadrant = ?"
                params.append(quadrant)

            if is_falsified is not None:
                query += " AND is_falsified = ?"
                params.append(is_falsified)

            query += f" ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            hands = []
            for row in rows:
                hand_dict = dict(zip(columns, row))
                # Parse JSON fields
                if hand_dict.get('auction_history'):
                    try:
                        hand_dict['auction_history'] = json.loads(hand_dict['auction_history'])
                    except:
                        pass
                hands.append(hand_dict)

            # Get total count with filters
            count_query = "SELECT COUNT(*) FROM imported_hands WHERE tournament_id = ?"
            count_params = [tournament_id]
            if audit_category:
                count_query += " AND audit_category = ?"
                count_params.append(audit_category)
            if quadrant:
                count_query += " AND quadrant = ?"
                count_params.append(quadrant)

            cursor.execute(count_query, count_params)
            total = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return jsonify({
                'hands': hands,
                'total': total,
                'tournament_id': tournament_id
            })

        except Exception as e:
            logger.exception(f"Error getting tournament hands: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # GET /api/tournaments/<id>/hands/<hand_id> - Get single hand detail
    # =========================================================================
    @app.route('/api/tournaments/<int:tournament_id>/hands/<int:hand_id>', methods=['GET'])
    def get_imported_hand_detail(tournament_id: int, hand_id: int):
        """
        Get full analysis for a single hand.

        Includes all audit data, DDS comparison, and educational feedback.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM imported_hands
                WHERE id = ? AND tournament_id = ?
            """, (hand_id, tournament_id))

            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Hand not found'}), 404

            columns = [desc[0] for desc in cursor.description]
            hand = dict(zip(columns, row))

            # Parse JSON fields
            json_fields = ['auction_history', 'deal_json', 'dds_analysis']
            for field in json_fields:
                if hand.get(field):
                    try:
                        hand[field] = json.loads(hand[field])
                    except:
                        pass

            cursor.close()
            conn.close()

            return jsonify(hand)

        except Exception as e:
            logger.exception(f"Error getting hand detail: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # POST /api/tournaments/<id>/analyze - Trigger analysis for tournament
    # =========================================================================
    @app.route('/api/tournaments/<int:tournament_id>/analyze', methods=['POST'])
    def analyze_tournament(tournament_id: int):
        """
        Trigger V3 engine analysis for all hands in a tournament.

        This runs the comparison between tournament results and engine logic,
        populating the audit columns for each hand.

        Note: For production, this should be queued as a background job.
        """
        try:
            data = request.get_json() or {}
            hero_position = data.get('hero_position', 'S')

            conn = get_connection()
            cursor = conn.cursor()

            # Update tournament status
            cursor.execute("""
                UPDATE imported_tournaments
                SET import_status = 'analyzing'
                WHERE id = ?
            """, (tournament_id,))

            # Get all pending hands
            cursor.execute("""
                SELECT id, hand_south, auction_history, vulnerability, dealer,
                       contract_level, contract_strain, contract_doubled,
                       tricks_taken, score_ns, board_number
                FROM imported_hands
                WHERE tournament_id = ? AND analysis_status = 'pending'
            """, (tournament_id,))

            hands = cursor.fetchall()
            analyzed_count = 0
            errors = []

            for hand_row in hands:
                hand_id = hand_row[0]
                try:
                    # Create PBNHand object
                    pbn_hand = PBNHand(
                        board_number=hand_row[10],
                        dealer=hand_row[4] or 'N',
                        vulnerability=hand_row[3] or 'None',
                        hands={hero_position: hand_row[1] or ''},
                        auction_history=json.loads(hand_row[2]) if hand_row[2] else [],
                        contract_level=hand_row[5] or 0,
                        contract_strain=hand_row[6] or '',
                        contract_doubled=hand_row[7] or 0,
                        tricks_taken=hand_row[8] or 0,
                        score_ns=hand_row[9] or 0
                    )

                    # Run V3 analysis
                    v3_result = analyze_pbn_hand_with_v3(pbn_hand, hero_position)

                    # Generate audit report
                    audit = generate_audit_report(pbn_hand, v3_result)

                    # Update hand record
                    cursor.execute("""
                        UPDATE imported_hands SET
                            optimal_bid = ?,
                            matched_rule = ?,
                            rule_tier = ?,
                            theoretical_score = ?,
                            panic_index = ?,
                            survival_status = ?,
                            rescue_action = ?,
                            is_logic_aligned = ?,
                            is_falsified = ?,
                            score_delta = ?,
                            potential_savings = ?,
                            bidding_efficiency = ?,
                            audit_category = ?,
                            educational_feedback = ?,
                            quadrant = ?,
                            analysis_status = 'complete',
                            analyzed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        audit.optimal_bid,
                        audit.matched_rule,
                        audit.rule_tier,
                        audit.theoretical_score,
                        audit.panic_index,
                        audit.survival_status,
                        audit.rescue_action,
                        1 if audit.is_logic_aligned else 0,
                        1 if audit.is_falsified else 0,
                        audit.score_delta,
                        audit.potential_savings,
                        audit.bidding_efficiency,
                        audit.audit_category,
                        audit.educational_feedback,
                        audit.quadrant,
                        hand_id
                    ))

                    analyzed_count += 1

                except Exception as e:
                    errors.append(f"Board {hand_row[10]}: {str(e)}")
                    cursor.execute("""
                        UPDATE imported_hands SET
                            analysis_status = 'failed',
                            analysis_error = ?
                        WHERE id = ?
                    """, (str(e), hand_id))

            # Update tournament statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_logic_aligned = 1 THEN 1 ELSE 0 END) as aligned,
                    SUM(potential_savings) as savings,
                    AVG(score_delta) as avg_delta
                FROM imported_hands
                WHERE tournament_id = ? AND analysis_status = 'complete'
            """, (tournament_id,))

            stats = cursor.fetchone()
            total, aligned, savings, avg_delta = stats

            alignment_rate = (aligned / total * 100) if total > 0 else 0

            cursor.execute("""
                UPDATE imported_tournaments SET
                    import_status = 'complete',
                    hands_analyzed = ?,
                    alignment_rate = ?,
                    total_potential_savings = ?,
                    average_score_delta = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (analyzed_count, alignment_rate, savings or 0, avg_delta or 0, tournament_id))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'tournament_id': tournament_id,
                'hands_analyzed': analyzed_count,
                'errors': errors[:10],
                'alignment_rate': alignment_rate,
                'total_potential_savings': savings or 0,
                'status': 'complete'
            })

        except Exception as e:
            logger.exception(f"Error analyzing tournament: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # GET /api/import-status/<id> - Check import/analysis progress
    # =========================================================================
    @app.route('/api/import-status/<int:tournament_id>', methods=['GET'])
    def get_import_status(tournament_id: int):
        """
        Check import and analysis progress for a tournament.

        Returns status, counts, and any errors.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT import_status, total_hands, hands_analyzed, import_error
                FROM imported_tournaments
                WHERE id = ?
            """, (tournament_id,))

            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Tournament not found'}), 404

            # Get analysis status breakdown
            cursor.execute("""
                SELECT analysis_status, COUNT(*) as count
                FROM imported_hands
                WHERE tournament_id = ?
                GROUP BY analysis_status
            """, (tournament_id,))

            status_breakdown = {}
            for status_row in cursor.fetchall():
                status_breakdown[status_row[0] or 'unknown'] = status_row[1]

            cursor.close()
            conn.close()

            return jsonify({
                'tournament_id': tournament_id,
                'import_status': row[0],
                'total_hands': row[1],
                'hands_analyzed': row[2],
                'import_error': row[3],
                'analysis_breakdown': status_breakdown,
                'progress_percent': (row[2] / row[1] * 100) if row[1] > 0 else 0
            })

        except Exception as e:
            logger.exception(f"Error getting import status: {e}")
            return jsonify({'error': str(e)}), 500

    # =========================================================================
    # DELETE /api/tournaments/<id> - Delete tournament
    # =========================================================================
    @app.route('/api/tournaments/<int:tournament_id>', methods=['DELETE'])
    def delete_tournament(tournament_id: int):
        """Delete a tournament and all associated hands."""
        try:
            user_id = request.args.get('user_id', type=int)

            conn = get_connection()
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute("""
                SELECT user_id FROM imported_tournaments WHERE id = ?
            """, (tournament_id,))

            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Tournament not found'}), 404

            if user_id and row[0] != user_id:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Access denied'}), 403

            # Delete hands first (FK constraint)
            cursor.execute("""
                DELETE FROM imported_hands WHERE tournament_id = ?
            """, (tournament_id,))

            hands_deleted = cursor.rowcount

            # Delete tournament
            cursor.execute("""
                DELETE FROM imported_tournaments WHERE id = ?
            """, (tournament_id,))

            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'success': True,
                'tournament_id': tournament_id,
                'hands_deleted': hands_deleted
            })

        except Exception as e:
            logger.exception(f"Error deleting tournament: {e}")
            return jsonify({'error': str(e)}), 500

    logger.info("ACBL Import API endpoints registered")
