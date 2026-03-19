import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import heapq
import tracemalloc
import os
import random
import sys

# =============================================================================
# 1. KHỞI TẠO HỆ THỐNG & ĐỌC THAM SỐ
# =============================================================================
if len(sys.argv) != 3:
    print("Cách dùng: python script.py <N> <A|B>")
    sys.exit(1)

try:
    N = int(sys.argv[1])
    algo = sys.argv[2].upper()
except ValueError:
    print("Lỗi: Tham số thứ nhất phải là một số nguyên")
    sys.exit(1)

if os.path.exists('output.txt'):
    os.remove('output.txt')

try:
    with open('Sudoku_Regions.txt') as f:
        content = f.read()
    dict_construct = 'regions_dict = {' + content + '}'
    regions_dict = {}
    exec(dict_construct)
except Exception as e:
    print(f"Lỗi khi đọc file Sudoku_Regions.txt: {e}")
    sys.exit(1)

numbers_set = set(range(1, N + 1))

# =============================================================================
# 2. CÁC HÀM HỖ TRỢ LOGIC
# =============================================================================

def construct_sudoku_array():
    with open('Sudoku.txt') as f:
        raw_data = f.read().replace(',', ' ').split()
        data = [int(x) for x in raw_data]
    if len(data) != N * N:
        raise ValueError(f"Dữ liệu trong Sudoku.txt không khớp với N={N}")
    return np.array(data, dtype=int).reshape(N, N)

def find_region(i, j):
    for v, d in regions_dict.items():
        if (i, j) in d:
            return v
    return None

def find_available_numbers(x, i, j):
    set_row = set(x[i, :])
    set_col = set(x[:, j])
    reg_id = find_region(i, j)
    set_region = set(x[p] for p in regions_dict[reg_id])
    used = set_row.union(set_col).union(set_region)
    return numbers_set.difference(used)

def find_empty(x):
    empty_cells = []
    for index, item in np.ndenumerate(x):
        if item == 0:
            available = find_available_numbers(x, index[0], index[1])
            empty_cells.append((index, len(available)))
    if not empty_cells: return None
    empty_cells.sort(key=lambda x: x[1])
    return empty_cells[0][0]

# =============================================================================
# 3. THUẬT TOÁN (DFS & A*)
# =============================================================================

def solve_dfs(sudoku_array, stats):
    empty_index = find_empty(sudoku_array)
    if not empty_index: return True
    row, col = empty_index
    available = find_available_numbers(sudoku_array, row, col)
    for num in sorted(list(available)):
        sudoku_array[row, col] = num
        display_sudoku(sudoku_array)
        root.update()
        stats['count'] += 1
        if solve_dfs(sudoku_array, stats): return True
        sudoku_array[row, col] = 0
        display_sudoku(sudoku_array)
        root.update()
    return False

def solve_with_metrics(sudoku_array):
    stats = {'count': 0, 'history': []}
    tracemalloc.start()
    start_time = time.time()
    solved = solve_dfs(sudoku_array, stats)
    tracemalloc.stop()
    return sudoku_array if solved else None

def calculate_heuristic(sudoku):
    h = 0
    for i in range(N):
        for j in range(N):
            if sudoku[i, j] == 0:
                available = find_available_numbers(sudoku, i, j)
                h += (1.0 / len(available)) if available else N*5
    return h

def a_star_optimized(initial):
    open_heap = []
    closed = set()
    sequence = 0
    heapq.heappush(open_heap, (calculate_heuristic(initial), sequence, initial.copy()))
    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current.tobytes() in closed: continue
        closed.add(current.tobytes())
        empty = find_empty(current)
        if not empty: return current
        r, c = empty
        for num in find_available_numbers(current, r, c):
            new_state = current.copy()
            new_state[r, c] = num
            sequence += 1
            heapq.heappush(open_heap, (calculate_heuristic(new_state), sequence, new_state))
    return None

# =============================================================================
# 4. GIAO DIỆN & CÁC NÚT ĐIỀU KHIỂN
# =============================================================================

def get_board_from_gui():
    """Lấy dữ liệu hiện tại từ các ô Entry trên màn hình"""
    board = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            val = entries[i][j].get()
            board[i, j] = int(val) if val.isdigit() else 0
    return board

def check_solution_command():
    """Kiểm tra xem bảng người dùng tự giải có đúng quy tắc không"""
    board = get_board_from_gui()
    
    # 1. Kiểm tra xem đã điền hết các ô chưa
    if np.any(board == 0):
        messagebox.showwarning("Incomplete", "Vui lòng điền hết tất cả các ô trống trước khi kiểm tra!")
        return

    # 2. Kiểm tra hàng và cột
    for i in range(N):
        if len(set(board[i, :])) != N:
            messagebox.showerror("Error", f"Hàng {i+1} có số bị trùng hoặc không hợp lệ!")
            return
        if len(set(board[:, i])) != N:
            messagebox.showerror("Error", f"Cột {i+1} có số bị trùng hoặc không hợp lệ!")
            return

    # 3. Kiểm tra các vùng (Jigsaw Regions)
    for reg_id, points in regions_dict.items():
        vals = [board[p] for p in points]
        if len(set(vals)) != N:
            messagebox.showerror("Error", f"Vùng '{reg_id}' có số bị trùng hoặc không hợp lệ!")
            return

    messagebox.showinfo("Success", "Chúc mừng! Bạn đã giải đúng bài toán Sudoku này.")

def solve_command():
    board = get_board_from_gui()
    result = a_star_optimized(board) if algo == "A" else solve_with_metrics(board)
    if result is not None:
        display_sudoku(result)
        messagebox.showinfo("Solved", "AI đã tìm ra đáp án!")
    else:
        messagebox.showwarning("Failed", "Không tìm thấy đáp án!")

def display_sudoku(matrix):
    for i in range(N):
        for j in range(N):
            reg_id = find_region(i, j)
            color = region_colors[region_to_color_idx[reg_id]]
            entries[i][j].delete(0, tk.END)
            entries[i][j].config(bg=color)
            if matrix[i, j] != 0:
                entries[i][j].insert(0, str(matrix[i, j]))

def reset_command():
    try:
        display_sudoku(construct_sudoku_array())
    except: pass

# Khởi tạo GUI
root = tk.Tk()
root.title(f"Jigsaw Sudoku {N}x{N}")
random.seed(42)
region_colors = ["#{:06x}".format(random.randint(0, 0xFFFFFF)) for _ in range(len(regions_dict))]
region_to_color_idx = {name: i for i, name in enumerate(regions_dict.keys())}

frame = tk.Frame(root)
frame.pack(pady=10, padx=10)

entries = [[None for _ in range(N)] for _ in range(N)]
for i in range(N):
    for j in range(N):
        e = tk.Entry(frame, width=3, font=('Arial', 18, 'bold'), justify='center', borderwidth=1, relief="solid")
        e.grid(row=i, column=j, ipady=8)
        entries[i][j] = e

# Cụm các nút bấm
btn_solve = tk.Button(root, text="AI SOLVE", command=solve_command, bg="#4CAF50", fg="white", width=25)
btn_solve.pack(pady=2)

btn_check = tk.Button(root, text="CHECK MY SOLUTION", command=check_solution_command, bg="#FF9800", fg="white", width=25)
btn_check.pack(pady=2)

btn_reset = tk.Button(root, text="RESET BOARD", command=reset_command, bg="#2196F3", fg="white", width=25)
btn_reset.pack(pady=2)

reset_command()
root.mainloop()