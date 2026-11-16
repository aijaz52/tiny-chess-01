import json
import os
import sys
import urllib.error
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

# --- Constants ---
WHITE, BLACK = 0, 1
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
PIECE_CHARS = ".PNBRQKpnbrqk"
VALUES = [0, 100, 320, 330, 500, 900, 20000]
PROMO_PIECES = [QUEEN, ROOK, BISHOP, KNIGHT]
INF = 32000
MATE = 30000

# 0x88 board helpers
def sq88(f, r):
    return r * 16 + f

def on_board(sq):
    return (sq & 0x88) == 0

def file_of(sq): return sq & 7
def rank_of(sq): return sq >> 4
def to_alg(sq):
    return "abcdefgh"[file_of(sq)] + str(rank_of(sq) + 1)

def from_alg(s):
    f = ord(s[0]) - 97
    r = int(s[1]) - 1
    return sq88(f, r)

# Directions
N, S, E, W = 16, -16, 1, -1
DIRS = {
    KNIGHT: [33, 31, 18, 14, -14, -18, -31, -33],
    BISHOP: [17, 15, -15, -17],
    ROOK: [16, -16, 1, -1],
    QUEEN: [17, 15, -15, -17, 16, -16, 1, -1],
    KING: [17, 15, -15, -17, 16, -16, 1, -1],
}

# Piece-square tables (from white perspective, rank 1..8 -> index 0..7 bottom to top)
def mirror(pst):
    return [pst[7 - (i >> 3)][i & 7] for i in range(64)]

def expand(tbl):
    # tbl given as 8 ranks from rank8 down to rank1 in human form? easier give 64 list from a1..h8
    return tbl

# PSTs: values in centipawns, indexed by square 0=a1..63=h8 from white POV
PST_P = [
    0,0,0,0,0,0,0,0,
    50,50,50,50,50,50,50,50,
    10,10,20,30,30,20,10,10,
    5,5,10,25,25,10,5,5,
    0,0,0,20,20,0,0,0,
    5,-5,-10,0,0,-10,-5,5,
    5,10,10,-20,-20,10,10,5,
    0,0,0,0,0,0,0,0,
]
PST_N = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,0,0,0,0,-20,-40,
    -30,0,10,15,15,10,0,-30,
    -30,5,15,20,20,15,5,-30,
    -30,0,15,20,20,15,0,-30,
    -30,5,10,15,15,10,5,-30,
    -40,-20,0,5,5,0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
PST_B = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,0,0,0,0,0,0,-10,
    -10,0,5,10,10,5,0,-10,
    -10,5,5,10,10,5,5,-10,
    -10,0,10,10,10,10,0,-10,
    -10,10,10,10,10,10,10,-10,
    -10,5,0,0,0,0,5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
PST_R = [
    0,0,0,0,0,0,0,0,
    5,10,10,10,10,10,10,5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    -5,0,0,0,0,0,0,-5,
    0,0,0,5,5,0,0,0,
]
PST_Q = [
    -20,-10,-10,-5,-5,-10,-10,-20,
    -10,0,0,0,0,0,0,-10,
    -10,0,5,5,5,5,0,-10,
    -5,0,5,5,5,5,0,-5,
    0,0,5,5,5,5,0,-5,
    -10,5,5,5,5,5,0,-10,
    -10,0,5,0,0,0,0,-10,
    -20,-10,-10,-5,-5,-10,-10,-20,
]
PST_K_MG = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20,20,0,0,0,0,20,20,
    20,30,10,0,0,10,30,20,
]
PST_K_EG = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,0,0,-10,-20,-30,
    -30,-10,20,30,30,20,-10,-30,
    -30,-10,30,40,40,30,-10,-30,
    -30,-10,30,40,40,30,-10,-30,
    -30,-10,20,30,30,20,-10,-30,
    -30,-30,0,0,0,0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]
PST = {
    PAWN: PST_P, KNIGHT: PST_N, BISHOP: PST_B, ROOK: PST_R, QUEEN: PST_Q, KING: PST_K_MG
}

PHASE_W = [0,0,1,1,2,4,0]

class State:
    __slots__ = ('board','side','castle','ep','king_sq','hash')
    def __init__(self):
        self.board = [0]*128
        self.side = WHITE
        self.castle = 0 # bits: 1 WK,2 WQ,4 BK,8 BQ
        self.ep = -1
        self.king_sq = [-1, -1]
        self.hash = 0

def piece_of(p): return p & 7
def color_of(p): return (p >> 3) & 1
def make_piece(c,t): return (c<<3)|t

def clone_state(s):
    n = State()
    n.board = s.board[:]
    n.side = s.side
    n.castle = s.castle
    n.ep = s.ep
    n.king_sq = s.king_sq[:]
    n.hash = s.hash
    return n

def parse_fen(fen):
    s = State()
    parts = fen.split()
    rows = parts[0].split('/')
    for r in range(8):
        f = 0
        rank = 7 - r
        for ch in rows[r]:
            if ch.isdigit():
                f += int(ch)
            else:
                color = WHITE if ch.isupper() else BLACK
                pt = {'p':PAWN,'n':KNIGHT,'b':BISHOP,'r':ROOK,'q':QUEEN,'k':KING}[ch.lower()]
                sq = sq88(f, rank)
                s.board[sq] = make_piece(color, pt)
                if pt == KING:
                    s.king_sq[color] = sq
                f += 1
    s.side = WHITE if parts[1] == 'w' else BLACK
    s.castle = 0
    if len(parts) > 2 and parts[2] != '-':
        for ch in parts[2]:
            s.castle |= {'K':1,'Q':2,'k':4,'q':8}.get(ch,0)
    s.ep = -1
    if len(parts) > 3 and parts[3] != '-':
        s.ep = from_alg(parts[3])
    return s

def is_attacked(s, sq, by_color):
    b = s.board
    # pawns
    if by_color == WHITE:
        for d in (-15, -17):
            t = sq + d
            if on_board(t):
                p = b[t]
                if p and color_of(p)==WHITE and piece_of(p)==PAWN: return True
    else:
        for d in (15, 17):
            t = sq + d
            if on_board(t):
                p = b[t]
                if p and color_of(p)==BLACK and piece_of(p)==PAWN: return True
    # knights
    for d in DIRS[KNIGHT]:
        t = sq + d
        if on_board(t):
            p = b[t]
            if p and color_of(p)==by_color and piece_of(p)==KNIGHT: return True
    # bishops/queens
    for d in DIRS[BISHOP]:
        t = sq + d
        while on_board(t):
            p = b[t]
            if p:
                if color_of(p)==by_color and piece_of(p) in (BISHOP, QUEEN): return True
                break
            t += d
    # rooks/queens
    for d in DIRS[ROOK]:
        t = sq + d
        while on_board(t):
            p = b[t]
            if p:
                if color_of(p)==by_color and piece_of(p) in (ROOK, QUEEN): return True
                break
            t += d
    # king
    for d in DIRS[KING]:
        t = sq + d
        if on_board(t):
            p = b[t]
            if p and color_of(p)==by_color and piece_of(p)==KING: return True
    return False

def in_check(s, color):
    k = s.king_sq[color]
    if k < 0: return False
    return is_attacked(s, k, color ^ 1)

# Move: (from,to,promo,capture_piece,flag)
# flags: 0 normal,1 ep,2 castle,3 promo

def generate_pseudo(s):
    moves = []
    b = s.board
    us = s.side
    opp = us ^ 1
    for r in range(8):
        for f in range(8):
            sq = sq88(f,r)
            p = b[sq]
            if not p or color_of(p) != us: continue
            pt = piece_of(p)
            if pt == PAWN:
                dir = 16 if us == WHITE else -16
                start_rank = 1 if us == WHITE else 6
                promo_rank = 7 if us == WHITE else 0
                one = sq + dir
                if on_board(one) and not b[one]:
                    if rank_of(one) == promo_rank:
                        for pr in PROMO_PIECES:
                            moves.append((sq,one,pr,0,3))
                    else:
                        moves.append((sq,one,0,0,0))
                        if rank_of(sq) == start_rank:
                            two = sq + dir*2
                            if on_board(two) and not b[two]:
                                moves.append((sq,two,0,0,0))
                for d in (dir-1, dir+1):
                    t = sq + d
                    if not on_board(t): continue
                    cap = b[t]
                    if cap and color_of(cap)==opp:
                        if rank_of(t) == promo_rank:
                            for pr in PROMO_PIECES:
                                moves.append((sq,t,pr,cap,3))
                        else:
                            moves.append((sq,t,0,cap,0))
                    elif t == s.ep and s.ep != -1:
                        # ep capture
                        cap_sq = t - dir
                        cap_p = b[cap_sq]
                        moves.append((sq,t,0,cap_p,1))
            elif pt == KNIGHT or pt == KING:
                for d in DIRS[pt]:
                    t = sq + d
                    if not on_board(t): continue
                    cap = b[t]
                    if cap and color_of(cap)==us: continue
                    moves.append((sq,t,0,cap,0))
                if pt == KING:
                    if us == WHITE:
                        if (s.castle & 1) and not b[sq88(5,0)] and not b[sq88(6,0)]:
                            if not is_attacked(s,sq88(4,0),BLACK) and not is_attacked(s,sq88(5,0),BLACK) and not is_attacked(s,sq88(6,0),BLACK):
                                moves.append((sq88(4,0),sq88(6,0),0,0,2))
                        if (s.castle & 2) and not b[sq88(3,0)] and not b[sq88(2,0)] and not b[sq88(1,0)]:
                            if not is_attacked(s,sq88(4,0),BLACK) and not is_attacked(s,sq88(3,0),BLACK) and not is_attacked(s,sq88(2,0),BLACK):
                                moves.append((sq88(4,0),sq88(2,0),0,0,2))
                    else:
                        if (s.castle & 4) and not b[sq88(5,7)] and not b[sq88(6,7)]:
                            if not is_attacked(s,sq88(4,7),WHITE) and not is_attacked(s,sq88(5,7),WHITE) and not is_attacked(s,sq88(6,7),WHITE):
                                moves.append((sq88(4,7),sq88(6,7),0,0,2))
                        if (s.castle & 8) and not b[sq88(3,7)] and not b[sq88(2,7)] and not b[sq88(1,7)]:
                            if not is_attacked(s,sq88(4,7),WHITE) and not is_attacked(s,sq88(3,7),WHITE) and not is_attacked(s,sq88(2,7),WHITE):
                                moves.append((sq88(4,7),sq88(2,7),0,0,2))
            else:
                for d in DIRS[pt]:
                    t = sq + d
                    while on_board(t):
                        cap = b[t]
                        if cap:
                            if color_of(cap)!=us:
                                moves.append((sq,t,0,cap,0))
                            break
                        moves.append((sq,t,0,0,0))
                        t += d
    return moves

def make_move(s, m):
    b = s.board
    fr,to,promo,cap,flag = m
    us = s.side
    p = b[fr]
    undo = (fr,to,promo,cap,flag,s.castle,s.ep,s.king_sq[us],s.king_sq[us^1])
    # update castle rights by moving/capturing rook or king
    def clear_castle_square(sq):
        if sq == sq88(0,0): s.castle &= ~2
        elif sq == sq88(7,0): s.castle &= ~1
        elif sq == sq88(0,7): s.castle &= ~8
        elif sq == sq88(7,7): s.castle &= ~4
        elif sq == sq88(4,0): s.castle &= ~3
        elif sq == sq88(4,7): s.castle &= ~12
    clear_castle_square(fr)
    if cap:
        clear_castle_square(to)
    s.ep = -1
    b[fr] = 0
    if flag == 1: # ep
        dir = 16 if us == WHITE else -16
        cap_sq = to - dir
        b[cap_sq] = 0
        b[to] = p
    elif flag == 2: # castle
        b[to] = p
        if to == sq88(6,0): b[sq88(5,0)] = b[sq88(7,0)]; b[sq88(7,0)] = 0
        elif to == sq88(2,0): b[sq88(3,0)] = b[sq88(0,0)]; b[sq88(0,0)] = 0
        elif to == sq88(6,7): b[sq88(5,7)] = b[sq88(7,7)]; b[sq88(7,7)] = 0
        elif to == sq88(2,7): b[sq88(3,7)] = b[sq88(0,7)]; b[sq88(0,7)] = 0
    elif flag == 3:
        b[to] = make_piece(us, promo)
    else:
        b[to] = p
        if piece_of(p) == PAWN and abs(to-fr) == 32:
            s.ep = (fr + to) // 2
    if piece_of(p) == KING:
        s.king_sq[us] = to
    s.side ^= 1
    return undo

def unmake_move(s, m, undo):
    b = s.board
    fr,to,promo,cap,flag,castle,ep,ks_us,ks_opp = undo
    us = s.side ^ 1
    s.side = us
    s.castle = castle
    s.ep = ep
    s.king_sq[us] = ks_us
    s.king_sq[us^1] = ks_opp
    p = b[to]
    if flag == 3:
        p = make_piece(us, PAWN)
    b[fr] = p
    b[to] = 0
    if flag == 1:
        dir = 16 if us == WHITE else -16
        cap_sq = to - dir
        b[cap_sq] = cap
    elif flag == 2:
        if to == sq88(6,0): b[sq88(7,0)] = b[sq88(5,0)]; b[sq88(5,0)] = 0
        elif to == sq88(2,0): b[sq88(0,0)] = b[sq88(3,0)]; b[sq88(3,0)] = 0
        elif to == sq88(6,7): b[sq88(7,7)] = b[sq88(5,7)]; b[sq88(5,7)] = 0
        elif to == sq88(2,7): b[sq88(0,7)] = b[sq88(3,7)]; b[sq88(3,7)] = 0
    else:
        if cap:
            b[to] = cap

def legal_moves(s):
    res = []
    us = s.side
    for m in generate_pseudo(s):
        u = make_move(s,m)
        if not in_check(s, us):
            res.append(m)
        unmake_move(s,m,u)
    return res

def move_to_uci(m):
    fr,to,promo,cap,flag = m
    u = to_alg(fr)+to_alg(to)
    if promo:
        u += {KNIGHT:'n',BISHOP:'b',ROOK:'r',QUEEN:'q'}[promo]
    return u

# --- Evaluation ---
def evaluate(s):
    b = s.board
    score_mg = 0
    score_eg = 0
    phase = 0
    bishops = [0,0]
    for r in range(8):
        for f in range(8):
            sq = sq88(f,r)
            p = b[sq]
            if not p: continue
            c = color_of(p); pt = piece_of(p)
            phase += PHASE_W[pt]
            val = VALUES[pt]
            idx = r*8+f if c==WHITE else (7-r)*8+f
            if pt == PAWN: pst_mg = pst_eg = PST_P[idx]
            elif pt == KNIGHT: pst_mg = pst_eg = PST_N[idx]
            elif pt == BISHOP: pst_mg = pst_eg = PST_B[idx]; bishops[c]+=1
            elif pt == ROOK: pst_mg = pst_eg = PST_R[idx]
            elif pt == QUEEN: pst_mg = pst_eg = PST_Q[idx]
            else:
                pst_mg = PST_K_MG[idx]; pst_eg = PST_K_EG[idx]
            sgn = 1 if c==WHITE else -1
            score_mg += sgn*(val + pst_mg)
            score_eg += sgn*(val + pst_eg)
    if bishops[WHITE]>=2: score_mg += 30; score_eg += 40
    if bishops[BLACK]>=2: score_mg -= 30; score_eg -= 40
    # taper
    phase = min(phase, 24)
    score = (score_mg*phase + score_eg*(24-phase)) // 24
    return score if s.side==WHITE else -score

# --- Search ---
TT = {}
KILLERS = [[None,None] for _ in range(64)]

def mvv_lva(m):
    fr,to,promo,cap,flag = m
    if not cap and flag!=1: return 0
    victim = piece_of(cap) if cap else PAWN
    attacker = 1 # approximate; cheap
    return victim*10 - attacker

def order_moves(moves, tt_move, ply):
    scored = []
    k1,k2 = KILLERS[ply] if ply < 64 else (None,None)
    for m in moves:
        sc = 0
        if tt_move and m == tt_move: sc = 1000000
        elif m[3] or m[4]==1: sc = 100000 + mvv_lva(m) + (100 if m[2]==QUEEN else 0)
        elif m == k1: sc = 90000
        elif m == k2: sc = 80000
        elif m[4]==3: sc = 70000 + m[2]
        scored.append((sc,m))
    scored.sort(key=lambda x: -x[0])
    return [m for _,m in scored]

NODES = 0
NODE_LIMIT = 30000
STOP = False

def qsearch(s, alpha, beta, ply):
    global NODES, STOP
    NODES += 1
    if NODES >= NODE_LIMIT:
        STOP = True
        return evaluate(s)
    stand = evaluate(s)
    if stand >= beta: return beta
    if stand > alpha: alpha = stand
    in_chk = in_check(s, s.side)
    moves = legal_moves(s)
    # in qsearch: captures/promotions, but if in check search all evasions
    if in_chk:
        pass # all legal moves
    else:
        moves = [m for m in moves if m[3] or m[4]==1 or m[4]==3]
    moves = order_moves(moves, None, ply)
    for m in moves:
        u = make_move(s,m)
        val = -qsearch(s, -beta, -alpha, ply+1)
        unmake_move(s,m,u)
        if STOP: return alpha
        if val >= beta: return beta
        if val > alpha: alpha = val
    if in_chk and not moves:
        return -MATE + ply
    return alpha

def negamax(s, depth, alpha, beta, ply):
    global NODES, STOP
    if STOP: return 0, None
    NODES += 1
    if NODES >= NODE_LIMIT:
        STOP = True
        return evaluate(s), None
    alpha_orig = alpha
    tt_move = None
    key = (fen_key(s), depth)
    entry = TT.get(key)
    if entry:
        tt_depth, tt_val, tt_flag, tt_move = entry
        if tt_depth >= depth:
            if tt_flag == 0: return tt_val, tt_move
            elif tt_flag == 1 and tt_val <= alpha: return tt_val, tt_move
            elif tt_flag == 2 and tt_val >= beta: return tt_val, tt_move
    in_chk = in_check(s, s.side)
    if depth <= 0 and not in_chk:
        return qsearch(s, alpha, beta, ply), None
    moves = legal_moves(s)
    if not moves:
        if in_chk:
            return -MATE + ply, None
        return 0, None
    moves = order_moves(moves, tt_move, ply)
    best_move = moves[0]
    best_val = -INF
    for m in moves:
        u = make_move(s,m)
        val, _ = negamax(s, depth-1, -beta, -alpha, ply+1)
        val = -val
        unmake_move(s,m,u)
        if STOP: break
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha: alpha = val
        if alpha >= beta:
            # killer
            if not m[3] and m[4]!=1 and ply < 64:
                if KILLERS[ply][0] != m:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = m
            break
    if not STOP:
        flag = 0
        if best_val <= alpha_orig: flag = 1
        elif best_val >= beta: flag = 2
        TT[key] = (depth, best_val, flag, best_move)
    return best_val, best_move

def fen_key(s):
    # simple key: piece placement + side + castle + ep
    b = tuple(s.board[i] for i in range(128) if (i & 0x88)==0)
    return (b, s.side, s.castle, s.ep)

def search_root(s, legal_uci_set, avoid_positions):
    global NODES, STOP, TT, KILLERS
    TT.clear()
    KILLERS = [[None,None] for _ in range(64)]
    NODES = 0
    STOP = False
    legal = legal_moves(s)
    if not legal:
        return None
    # filter to env legal moves if provided
    candidates = [m for m in legal if move_to_uci(m) in legal_uci_set] or legal
    best_move = candidates[0]
    best_completed = candidates[0]
    # root repetition avoidance: prefer moves not leading to 3rd repetition
    for depth in range(1, 64):
        # aspiration not needed
        val, mv = negamax(s, depth, -INF, INF, 0)
        if mv and move_to_uci(mv) in (legal_uci_set or {move_to_uci(x) for x in candidates}):
            best_move = mv
        if not STOP:
            best_completed = best_move
        # try to avoid repetition at root among top choices by rescoring? simple: if best leads to repetition and there is alternative
        if STOP:
            break
    chosen = best_completed
    # root repetition avoidance check
    safe = None
    for m in candidates:
        u = make_move(s,m)
        k = fen_key(s)
        rep = avoid_positions.get(k, 0)
        unmake_move(s,m,u)
        if rep >= 2:
            continue
        if safe is None:
            safe = m
    # if chosen leads to repetition and safe alternative exists, pick safe best by quick eval
    u = make_move(s, chosen)
    ck = fen_key(s)
    repc = avoid_positions.get(ck,0)
    unmake_move(s, chosen, u)
    if repc >= 2 and safe is not None:
        chosen = safe
    # ensure chosen is in legal_uci_set
    if legal_uci_set and move_to_uci(chosen) not in legal_uci_set:
        for m in candidates:
            if move_to_uci(m) in legal_uci_set:
                chosen = m; break
    return chosen

# --- repetition tracking from move history ---
def compute_repetitions(moves_uci, max_plies=None):
    # play from startpos and count position occurrences
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    s = parse_fen(start_fen)
    counts = {}
    def add():
        k = fen_key(s)
        counts[k] = counts.get(k,0)+1
    add()
    seq = moves_uci if max_plies is None else moves_uci[:max_plies]
    for u in seq:
        lm = legal_moves(s)
        mm = None
        for m in lm:
            if move_to_uci(m)==u:
                mm = m; break
        if mm is None:
            # try parse directly
            fr = from_alg(u[:2]); to = from_alg(u[2:4])
            promo = 0
            if len(u)==5:
                promo = {'n':KNIGHT,'b':BISHOP,'r':ROOK,'q':QUEEN}[u[4]]
            for m in lm:
                if m[0]==fr and m[1]==to and m[2]==promo:
                    mm=m; break
        if mm is None:
            break
        make_move(s,mm)
        add()
    return counts, s

# --- HTTP loop ---
def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")

def choose_move(g):
    fen = g["fen"]
    s = parse_fen(fen)
    legal_env = g.get("legal_moves") or []
    legal_set = set(legal_env)
    # repetition counts from history (positions seen so far)
    hist = g.get("moves") or []
    reps, _ = compute_repetitions(hist)
    mv = search_root(s, legal_set, reps)
    if mv is None:
        return legal_env[0] if legal_env else "0000"
    u = move_to_uci(mv)
    if legal_env and u not in legal_set:
        # fallback
        own = {move_to_uci(m):m for m in legal_moves(s)}
        for lu in legal_env:
            if lu in own:
                return lu
        return legal_env[0]
    return u

def main():
    while True:
        g = post("/game", {})
        if g.get("status") == "done":
            break
        while g.get("status") == "your_move":
            move = choose_move(g)
            g = post("/move", {"game": g["game"], "move": move})
        if "outcome" in g:
            print(f"game {g.get('game')}: {g['outcome']} by {g.get('reason')}", file=sys.stderr)
    print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost", file=sys.stderr)

if __name__ == "__main__":
    main()
