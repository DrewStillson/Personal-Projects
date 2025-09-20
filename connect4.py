"""
Connect 4 (Pygame)
----------------------------------------------------------------
- Two Player mode
- Player vs Computer (minimax + alpha-beta)
"""

import sys
import math
import random
import pygame
import numpy as np

# -----------------------
# Global Config / Colors
# -----------------------

ROW_COUNT = 6
COLUMN_COUNT = 7
SQUARESIZE = 100

WIDTH = SQUARESIZE * COLUMN_COUNT
HEIGHT = SQUARESIZE * (ROW_COUNT + 2)  # +1 top bar +1 bottom bar

EMPTY = 0
PLAYER = 1
COMPUTER = 2

BLUE   = (0, 0, 255)
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
RED    = (255, 0, 0)       # player discs
YELLOW = (255, 255, 0)     # computer discs
GREEN  = (0, 255, 0)

AI_DEPTH = 5
AI_DELAY_MS = 250

# Fonts
TITLE_FONT = None
UI_FONT = None


# -------------
# Pygame Setup
# -------------

def init_pygame():
    """Initialize pygame, fonts, and the main window."""
    global TITLE_FONT, UI_FONT
    pygame.init()
    pygame.display.set_caption("Connect 4!")
    TITLE_FONT = pygame.font.SysFont("cooperblack", 75)
    UI_FONT = pygame.font.SysFont("cooperblack", 36)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    return screen


# ----------------------
# Board Helper Functions
# ----------------------

def create_board():
    """Create an empty board (ROW_COUNT x COLUMN_COUNT) filled with zeros."""
    return np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=int)

def valid_locations(board):
    """Return a list of columns that are not full."""
    cols = []
    for c in range(COLUMN_COUNT):
        if check_available_row(board, c) is not None:
            cols.append(c)
    return cols

def check_available_row(board, column):
    """
    Return the first empty row index in the given column
    (0 is bottom, ROW_COUNT-1 is top). If full, return None.
    """
    if column < 0 or column >= COLUMN_COUNT:
        return None
    for r in range(ROW_COUNT):
        if board[r, column] == EMPTY:
            return r
    return None

def place_piece(board, column, row, player_value):
    """Place a piece for the given player at (row, column)."""
    if row is None:
        return False
    board[row, column] = player_value
    return True

def board_full(board):
    """True if the board has no EMPTY cells."""
    return not (board == EMPTY).any()

def check_any_win(board, player_value):
    """Check if the given player has a winning 4-in-a-row anywhere."""
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT):
            if board[r, c] == player_value and check_win(board, r, c):
                return True
    return False

def check_win(board, piece_row, piece_column):
    """
    Check if there is a 4-in-a-row that includes the piece at (piece_row, piece_column).
    """
    piece = board[piece_row, piece_column]

    # Horizontal 4
    for c in range(COLUMN_COUNT - 3):
        if all(board[piece_row, c + i] == piece for i in range(4)):
            return True

    # Vertical 4
    for r in range(ROW_COUNT - 3):
        if all(board[r + i, piece_column] == piece for i in range(4)):
            return True

    # Diagonal down-right
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            if all(board[r + i, c + i] == piece for i in range(4)):
                return True

    # Diagonal up-right
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if all(board[r - i, c + i] == piece for i in range(4)):
                return True

    return False

def is_terminal(board):
    """
    Return (game_over, winner):
      - If someone won: (True, PLAYER/COMPUTER)
      - If draw: (True, None)
      - Else: (False, None)
    """
    if check_any_win(board, PLAYER):
        return True, PLAYER
    if check_any_win(board, COMPUTER):
        return True, COMPUTER
    if board_full(board):
        return True, None
    return False, None


# -----------------------
# Heuristic / Evaluation
# -----------------------

def peek_score(window, player_value):
    """
    Score a 4-cell window for `player_value`.
    Positive score favors the player; negative favors the opponent.
    """
    opp = PLAYER if player_value == COMPUTER else COMPUTER
    score = 0

    if window.count(player_value) == 4:
        score += 100000
    elif window.count(player_value) == 3 and window.count(EMPTY) == 1:
        score += 100
    elif window.count(player_value) == 2 and window.count(EMPTY) == 2:
        score += 10

    if window.count(opp) == 3 and window.count(EMPTY) == 1:
        score -= 120  # prefer blocking threats
    elif window.count(opp) == 2 and window.count(EMPTY) == 2:
        score -= 15

    return score

def position_score(board, player_value):
    """
    Evaluate a board:
    - Prefer center column
    - Score all horizontal, vertical, and diagonal 4-windows
    """
    score = 0

    # Center preference
    center_col = list(board[:, COLUMN_COUNT // 2])
    score += 10 * center_col.count(player_value)

    # Horizontal windows
    for r in range(ROW_COUNT):
        row_arr = list(board[r, :])
        for c in range(COLUMN_COUNT - 3):
            score += peek_score(row_arr[c:c+4], player_value)

    # Vertical windows
    for c in range(COLUMN_COUNT):
        col_arr = list(board[:, c])
        for r in range(ROW_COUNT - 3):
            score += peek_score(col_arr[r:r+4], player_value)

    # Diagonal down-right
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+i, c+i] for i in range(4)]
            score += peek_score(window, player_value)

    # Diagonal up-right
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+3-i, c+i] for i in range(4)]
            score += peek_score(window, player_value)

    return score


# -------------
# AI Utilities
# -------------

def ordered_columns():
    """Try center first, then expanding outward (3,2,4,1,5,0,6 for 7 cols)."""
    center = COLUMN_COUNT // 2
    order = [center]
    offset = 1
    while len(order) < COLUMN_COUNT:
        if center - offset >= 0: order.append(center - offset)
        if center + offset < COLUMN_COUNT: order.append(center + offset)
        offset += 1
    return order

def simulate_drop(board, col, player_value):
    """
    Simulate dropping a piece into `col` for `player_value`.
    Returns (tmp_board, row) or (None, None) if column is full.
    """
    r = check_available_row(board, col)
    if r is None:
        return None, None
    tmp = board.copy()
    place_piece(tmp, col, r, player_value)
    return tmp, r

def winning_moves(board, player_value):
    """Return a list of columns that immediately win for `player_value`."""
    wins = []
    for c in valid_locations(board):
        tmp, r = simulate_drop(board, c, player_value)
        if tmp is not None and check_win(tmp, r, c):
            wins.append(c)
    return wins


# -------------
# AI (Minimax)
# -------------

def minimax(board, depth, alpha, beta, maximizing):
    """
    Minimax with alpha-beta pruning.
    Returns (score, chosen_column). AI plays as COMPUTER.
    """
    game_over, winner = is_terminal(board)
    if depth == 0 or game_over:
        if game_over:
            if winner == COMPUTER:
                return (math.inf, None)
            elif winner == PLAYER:
                return (-math.inf, None)
            else:
                return (0, None)  # draw
        # Heuristic evaluation
        return (float(position_score(board, COMPUTER)), None)

    valid = valid_locations(board)
    order = [c for c in ordered_columns() if c in valid]

    if maximizing:
        value, best_col = -math.inf, None

        # Early shortcut: take immediate winning move if available
        for c in order:
            tmp, r = simulate_drop(board, c, COMPUTER)
            if tmp is not None and check_win(tmp, r, c):
                return (math.inf, c)

        for c in order:
            tmp, r = simulate_drop(board, c, COMPUTER)
            new_score, _ = minimax(tmp, depth - 1, alpha, beta, False)
            if new_score > value:
                value, best_col = new_score, c
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        if best_col is None:
            best_col = random.choice(valid)
        return (value, best_col)

    else:
        value, best_col = math.inf, None

        # Early shortcut: if opponent can win immediately by playing here,
        # treat that as worst outcome
        for c in order:
            tmp, r = simulate_drop(board, c, PLAYER)
            if tmp is not None and check_win(tmp, r, c):
                return (-math.inf, c)

        for c in order:
            tmp, r = simulate_drop(board, c, PLAYER)
            new_score, _ = minimax(tmp, depth - 1, alpha, beta, True)
            if new_score < value:
                value, best_col = new_score, c
            beta = min(beta, value)
            if alpha >= beta:
                break
        if best_col is None:
            best_col = random.choice(valid)
        return (value, best_col)

def ai_best_move(board):
    """Pick the best move for the COMPUTER using quick tactical checks + minimax."""
    # 1) Win now
    wins = winning_moves(board, COMPUTER)
    if wins:
        return wins[0]

    # 2) Block opponent win
    opp_wins = winning_moves(board, PLAYER)
    if opp_wins:
        return opp_wins[0]

    # 3) Otherwise search
    _, col = minimax(board, AI_DEPTH, -math.inf, math.inf, True)
    return col if col is not None else random.choice(valid_locations(board))


# ----------
# Rendering
# ----------

def draw_board(board, screen):
    """
    Draw the board grid and the discs.
    Flip the row for display, so row 0 (bottom in data) appears at the bottom.
    """
    # Grid and empty holes
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            pygame.draw.rect(screen, BLUE,
                             (c*SQUARESIZE, (r+1)*SQUARESIZE, SQUARESIZE, SQUARESIZE))
            pygame.draw.circle(screen, BLACK,
                               (c*SQUARESIZE + SQUARESIZE//2, (r+1)*SQUARESIZE + SQUARESIZE//2),
                               SQUARESIZE//2 - 5)

    # Discs (flip row)
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            display_r = ROW_COUNT - 1 - r
            if board[r, c] == PLAYER:
                color = RED
            elif board[r, c] == COMPUTER:
                color = YELLOW
            else:
                continue
            pygame.draw.circle(screen, color,
                               (c*SQUARESIZE + SQUARESIZE//2,
                                (display_r+1)*SQUARESIZE + SQUARESIZE//2),
                               SQUARESIZE//2 - 5)

    pygame.display.update()

def draw_bar_text(screen, text, color, y):
    """Draw a text bar across the width at vertical offset y."""
    pygame.draw.rect(screen, BLACK, (0, y, WIDTH, SQUARESIZE))
    label = UI_FONT.render(text, True, color)
    screen.blit(label, (20, y + 10))
    pygame.display.update(pygame.Rect(0, y, WIDTH, SQUARESIZE))

def clear_bottom_bar(screen):
    """Erase the rematch bar so it doesn't linger."""
    bar = pygame.Rect(0, HEIGHT - SQUARESIZE, WIDTH, SQUARESIZE)
    pygame.draw.rect(screen, BLACK, bar)
    pygame.display.update(bar)

def col_from_mouse(x):
    """Convert mouse x-position to board column index."""
    return x // SQUARESIZE


# ----------
# UI: Menu
# ----------

def main_menu(screen):
    """
    Main menu loop. Returns:
      0 -> Two Player
      1 -> Versus Computer
      2 -> Exit
    """
    while True:
        screen.fill(BLACK)
        title = TITLE_FONT.render("CONNECT 4!", True, WHITE)
        screen.blit(title, (100, 0))

        # Base labels
        two_p = UI_FONT.render("Play 2 Player", True, WHITE)
        ai_p  = UI_FONT.render("Play Computer", True, WHITE)
        ex_p  = UI_FONT.render("Exit", True, WHITE)
        screen.blit(two_p, (100, 200))
        screen.blit(ai_p,  (100, 400))
        screen.blit(ex_p,  (100, 600))

        # Hover feedback
        mx, my = pygame.mouse.get_pos()
        if 100 <= mx <= 600 and 200 <= my <= 300:
            screen.blit(UI_FONT.render("Play 2 Player", True, YELLOW), (100, 200))
        elif 100 <= mx <= 675 and 400 <= my <= 500:
            screen.blit(UI_FONT.render("Play Computer", True, BLUE), (100, 400))
        elif 100 <= mx <= 250 and 600 <= my <= 700:
            screen.blit(UI_FONT.render("Exit", True, RED), (100, 600))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 100 <= mx <= 600 and 200 <= my <= 300:
                    return 0
                elif 100 <= mx <= 675 and 400 <= my <= 500:
                    return 1
                elif 100 <= mx <= 250 and 600 <= my <= 700:
                    return 2


# --------------
# UI: Rematch UI
# --------------

def rematch(screen, mode_tag):
    """
    Rematch prompt at the bottom bar (text buttons with aligned hitboxes).
    Returns:
      mode_tag  -> rematch same mode
      "menu"    -> go back to main menu
      None      -> keep waiting (no click yet)
    """
    bar = pygame.Rect(0, HEIGHT - SQUARESIZE, WIDTH, SQUARESIZE)
    pygame.draw.rect(screen, BLACK, bar)

    # Render text pieces
    prompt_surf = UI_FONT.render("Rematch?", True, WHITE)
    yes_surf    = UI_FONT.render("Yes", True, WHITE)
    no_surf     = UI_FONT.render("No",  True, WHITE)

    # Place them in one row, left-aligned with padding
    padding_x = 20
    padding_y = 10
    y = HEIGHT - SQUARESIZE + padding_y

    prompt_rect = prompt_surf.get_rect()
    prompt_rect.topleft = (padding_x, y)

    yes_rect = yes_surf.get_rect()
    yes_rect.topleft = (prompt_rect.right + 30, y)

    no_rect = no_surf.get_rect()
    no_rect.topleft = (yes_rect.right + 40, y)

    # Hover highlighting by re-rendering the exact same rects
    mx, my = pygame.mouse.get_pos()
    yes_hover = yes_rect.collidepoint(mx, my)
    no_hover  = no_rect.collidepoint(mx, my)

    if yes_hover:
        yes_surf = UI_FONT.render("Yes", True, GREEN)
    if no_hover:
        no_surf  = UI_FONT.render("No",  True, RED)

    # Blit in order
    screen.blit(prompt_surf, prompt_rect.topleft)
    screen.blit(yes_surf,    yes_rect.topleft)
    screen.blit(no_surf,     no_rect.topleft)

    pygame.display.update(bar)

    # Handle clicks (use event.pos to avoid mismatch if mouse moves)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            ex, ey = event.pos
            if yes_rect.collidepoint(ex, ey):
                clear_bottom_bar(screen)   # make the bar disappear immediately
                return mode_tag
            if no_rect.collidepoint(ex, ey):
                clear_bottom_bar(screen)
                return "menu"

    return None


# -----------------
# Game Mode: 2P
# -----------------

def two_player(screen):
    """Two-player hotseat game mode. Returns next state token."""
    board = create_board()
    turn = 0
    winner = None
    draw = False

    clear_bottom_bar(screen)  # ensure rematch bar is gone when start

    while winner is None and not draw:
        player = PLAYER if turn % 2 == 0 else COMPUTER
        color = RED if player == PLAYER else YELLOW

        draw_board(board, screen)
        draw_bar_text(screen, f"Player {1 if player == PLAYER else 2}'s Turn", color, y=0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                col = col_from_mouse(event.pos[0])
                if 0 <= col < COLUMN_COUNT:
                    row = check_available_row(board, col)
                    if place_piece(board, col, row, player):
                        # find the filled row from the top for win check
                        check_row = next((r for r in range(ROW_COUNT - 1, -1, -1)
                                          if board[r, col] == player), 0)
                        if check_win(board, check_row, col):
                            winner = player
                        else:
                            game_over, _ = is_terminal(board)
                            draw = game_over and winner is None
                            turn += 1

    # End state screen
    draw_board(board, screen)
    if winner == PLAYER:
        draw_bar_text(screen, "Player 1 Wins!!", RED, y=0)
    elif winner == COMPUTER:
        draw_bar_text(screen, "Player 2 Wins!!", YELLOW, y=0)
    else:
        draw_bar_text(screen, "It's a Draw!!", WHITE, y=0)
    pygame.time.wait(1500)

    # Rematch loop (poll until a choice is made)
    while True:
        res = rematch(screen, mode_tag="2p")
        if res is None:
            continue
        if res == "2p":
            return "2p"
        if res == "menu":
            return "menu"


# -----------------------
# Game Mode: vs Computer
# -----------------------

def play_computer(screen):
    """Player (RED) vs Computer (YELLOW). Returns next state token."""
    board = create_board()
    turn = random.randint(0, 1)  # 0 -> PLAYER first, 1 -> COMPUTER first
    winner = None
    draw = False

    clear_bottom_bar(screen)  # ensure rematch bar is gone when start

    while winner is None and not draw:
        player = PLAYER if turn % 2 == 0 else COMPUTER
        color = RED if player == PLAYER else YELLOW

        draw_board(board, screen)
        if player == PLAYER:
            draw_bar_text(screen, "Player's Turn", color, y=0)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    col = col_from_mouse(event.pos[0])
                    if 0 <= col < COLUMN_COUNT:
                        row = check_available_row(board, col)
                        if place_piece(board, col, row, player):
                            check_row = next((r for r in range(ROW_COUNT - 1, -1, -1)
                                              if board[r, col] == player), 0)
                            if check_win(board, check_row, col):
                                winner = player
                            else:
                                game_over, _ = is_terminal(board)
                                draw = game_over and winner is None
                                turn += 1
        else:
            draw_bar_text(screen, "Computer's Turn", color, y=0)
            pygame.display.update()
            pygame.time.wait(AI_DELAY_MS)

            # AI move (with immediate win/block heuristics)
            col = ai_best_move(board)
            row = check_available_row(board, col)
            if place_piece(board, col, row, player):
                check_row = next((r for r in range(ROW_COUNT - 1, -1, -1)
                                  if board[r, col] == player), 0)
                if check_win(board, check_row, col):
                    winner = player
                else:
                    game_over, _ = is_terminal(board)
                    draw = game_over and winner is None
                    turn += 1

    # End state screen
    draw_board(board, screen)
    if winner == PLAYER:
        draw_bar_text(screen, "Player Wins!!", RED, y=0)
    elif winner == COMPUTER:
        draw_bar_text(screen, "Computer Wins!!", YELLOW, y=0)
    else:
        draw_bar_text(screen, "It's a Draw!!", WHITE, y=0)
    pygame.time.wait(1500)

    while True:
        res = rematch(screen, mode_tag="ai")
        if res is None:
            continue
        if res == "ai":
            return "ai"
        if res == "menu":
            return "menu"


# -------------
# App Orchestration
# -------------

def play_game():
    """Main app loop: menu -> game mode -> rematch/menu -> ..."""
    screen = init_pygame()

    while True:
        choice = main_menu(screen)
        if choice == 2:
            break

        if choice == 0:
            next_state = two_player(screen)
        else:
            next_state = play_computer(screen)

        if next_state is None:
            break
        if next_state == "menu":
            # go back to main menu
            continue
        if next_state in ("2p", "ai"):
            # rematch same mode
            if next_state == "2p":
                next_state = two_player(screen)
            else:
                next_state = play_computer(screen)

def main():
    try:
        play_game()
    finally:
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()
