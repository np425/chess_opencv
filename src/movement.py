import logging
from typing import List, Optional, Tuple
import chess
from . import robot
from .board import RealBoard, SQUARE_CENTER

logger = logging.getLogger(__name__)

def reflect_move(board: RealBoard, move: chess.Move) -> int:
    """
    Makes move physically, does not save the move in board
    """

    response = robot.COMMAND_SUCCESS
    from_square, to_square = (move.from_square, move.to_square)

    if board.chess_board.is_castling(move):
        rook_move = castle_rook_move(board.chess_board, move)
        if not rook_move:
            return robot.COMMAND_FAILURE

        response = move_piece(board, from_square, to_square, response)
        response = move_piece(board, rook_move.from_square, rook_move.to_square, response)
    else:  # Regular moves
        if board.chess_board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, to_square, off_board_place, response)
        if board.chess_board.is_en_passant(move):
            captured_square = en_passant_captured(move)
            captured_piece = board.piece_at(captured_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, captured_square, off_board_place, response)
        if move.promotion:
            removed_piece = board.piece_at(move.from_square)
            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = robot.off_board_square(piece_type, color)
            off_board_place_promoted = robot.off_board_square(
                move.promotion, color
            )

            # Remove original piece off the board
            response = move_piece(board, from_square, off_board_place_removed, response)

            # Set new piece to be moved
            from_square = off_board_place_promoted

        response = move_piece(board, from_square, to_square, response)

    return response

def move_piece(board: RealBoard, from_square: chess.Square, to_square: chess.Square, prev_response=robot.COMMAND_SUCCESS) -> int:
    """Assume move is valid, call before pushing move in memory!"""
    if prev_response == robot.COMMAND_SUCCESS:
        offset = board.offset(from_square)

        command = robot.form_command(from_square, to_square, offset, perspective=board.perspective)
        response = robot.issue_command(command)

        from_str = chess.square_name(from_square) if 0 <= from_square <= 63 else from_square
        to_str = chess.square_name(to_square) if 0 <= to_square <= 63 else to_square
        move_str = f"{from_str} -> {to_str}"

        if response == robot.COMMAND_SUCCESS:
            # Update board offsets
            if 0 <= from_square <= 63:
                board.set_offset(from_square, SQUARE_CENTER)

            if 0 <= to_square <= 63:
                board.set_offset(to_square, SQUARE_CENTER)

            logger.info(f"Moved piece {move_str} success")
        else:
            logger.warning(f"Moved piece {move_str} failed!")

        return response
    else:
        return prev_response

def identify_move(prev_board: chess.Board, current_board: chess.Board) -> Optional[chess.Move]:
    """
    Don't forget to validate move afterwards before using it
    """

    # Find piece differences
    dissapeared: List[chess.Square] = []
    appeared: List[chess.Square] = []

    for square in chess.SQUARES:
        prev_piece = prev_board.piece_at(square)
        curr_piece = current_board.piece_at(square)

        if prev_piece != curr_piece:
            if prev_piece is not None and curr_piece is None:
                dissapeared.append(square)
            else: # New piece or captured
                appeared.append(square)

    # Validate normal and promotion moves
    if len(dissapeared) == 1 and len(appeared) == 1:
        move = chess.Move(dissapeared[0], appeared[0])

        # En passant exception
        if is_en_passant(prev_board, move):
            return None
            
        # Castling exception
        if prev_board.is_castling(move):
            return None
        
        # Check for promotion
        if prev_board.piece_at(move.from_square).piece_type == chess.PAWN and chess.square_rank(move.to_square) in (0,7):
            promotion_piece = current_board.piece_at(move.to_square)

            # Validate promotion piece
            if not promotion_piece or prev_board.piece_at(move.from_square).color != promotion_piece.color:
                return None

            move.promotion = promotion_piece.piece_type

        return move

    # Validate castling move
    elif len(dissapeared) == 2 and len(appeared) == 2:
        if prev_board.piece_at(dissapeared[0]).piece_type != chess.KING:
            dissapeared = [dissapeared[1], dissapeared[0]]
        if current_board.piece_at(appeared[0]).piece_type != chess.KING:
            appeared = [appeared[1], appeared[0]]

        king_move = chess.Move(dissapeared[0], appeared[0])
        rook_move = chess.Move(dissapeared[1], appeared[1])

        if not prev_board.is_castling(king_move):
            return None 
        
        # Rook checks
        color = prev_board.piece_at(king_move.from_square).color
        expected_rook = chess.Piece(chess.ROOK, color)

        if prev_board.piece_at(rook_move.from_square) != expected_rook or current_board.piece_at(rook_move.to_square) != expected_rook:
            return None
        
        if rook_move != castle_rook_move(prev_board, king_move):
            return None

        return king_move

    # Validate en passant
    elif len(dissapeared) == 2 and len(appeared) == 1:
        pawn_move_to = appeared[0]
        if prev_board.is_en_passant(chess.Move(dissapeared[0], pawn_move_to)):
            pawn_move_from = dissapeared[0]
            en_passant_square = dissapeared[1]
        elif prev_board.is_en_passant(chess.Move(dissapeared[1], pawn_move_to)):
            pawn_move_from = dissapeared[1]
            en_passant_square = dissapeared[0]
        else:
            return None

        move = chess.Move(pawn_move_from, pawn_move_to)

        if en_passant_captured(move) != en_passant_square:
            return None

        return move

    return None
 
def castle_rook_move(board: chess.Board, king_move: chess.Move) -> Optional[chess.Move]:
    if board.piece_at(king_move.from_square).piece_type == chess.KING and board.is_castling(king_move):
        rook_from, rook_to = None, None
        if king_move.to_square == chess.G1:  # White kingside
            rook_from = chess.H1
            rook_to = chess.F1
        elif king_move.to_square == chess.C1:  # White queenside
            rook_from = chess.A1
            rook_to = chess.D1
        elif king_move.to_square == chess.G8:  # Black kingside
            rook_from = chess.H8
            rook_to = chess.F8
        elif king_move.to_square == chess.C8:  # Black queenside
            rook_from = chess.A8
            rook_to = chess.D8
        else:
            return None

        return chess.Move(rook_from, rook_to)
    return None


def en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square

def is_en_passant(board, move):
    if board.piece_at(move.from_square).piece_type == chess.PAWN:
        if abs(move.from_square - move.to_square) in (7, 9) and not board.piece_at(move.to_square):
            return True
    return False

def iter_reset_board(board: RealBoard, expected_board: RealBoard) -> Tuple[int, bool]:
    """
    Resets the board to match the expected_board configuration.
    If no expected_board is provided, it resets to the default chess starting position.
    If perspective is provided, adjusts the perspective accordingly.
    """
    # Create mappings for current and expected piece positions
    current_positions = {square: board.piece_at(square) for square in chess.SQUARES if board.piece_at(square)}
    expected_positions = {square: expected_board.piece_at(square) for square in chess.SQUARES if expected_board.piece_at(square)}

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {square: piece for square, piece in expected_positions.items() if current_positions.get(square) == piece}

    # Remove correctly placed pieces from current and expected mappings
    for square in list(correctly_placed.keys()):
        current_positions.pop(square, None)
        expected_positions.pop(square, None)

    # Use list to track empty squares on the board
    empty_squares = [square for square in chess.SQUARES if square not in current_positions and square not in expected_positions]

    # Helper function to move a piece and update mappings
    def move_piece_and_update(start_square: chess.Square, end_square: chess.Square) -> int:
        piece = board.piece_at(start_square)
        response = move_piece(board, start_square, end_square)
        if response != robot.COMMAND_SUCCESS:
            return response

        current_positions.pop(start_square)
        current_positions[end_square] = piece

        if end_square in expected_positions and expected_positions[end_square] == piece:
            expected_positions.pop(end_square)

        return robot.COMMAND_SUCCESS

    # First pass: move pieces directly to their target positions if possible
    for square, piece in list(expected_positions.items()):
        if piece in current_positions.values():
            for start_square, current_piece in list(current_positions.items()):
                if current_piece == piece:
                    response = move_piece_and_update(start_square, square)
                    return response, False

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in list(current_positions.items()):
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                response = move_piece_and_update(start_square, temp_square)
                return response, False

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in list(expected_positions.items()):
        origin_square = None
        for temp_square, current_piece in list(current_positions.items()):
            if current_piece == piece:
                origin_square = temp_square
                break
        if origin_square is None:
            origin_square = robot.off_board_square(piece.piece_type, piece.color)
        response = move_piece_and_update(origin_square, square)
        return response, False

    board.chess_board = expected_board.chess_board
    board.perspective = expected_board.perspective

    return robot.COMMAND_SUCCESS, True

