import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import heapq
import tracemalloc
import os
import random
import sys

# ==========================================
# KHỞI TẠO VÀ ĐỌC DỮ LIỆU
# ==========================================
if len(sys.argv) != 3:
    print("Cách dùng: python main.py <N> <A|B>")
    sys.exit(1)

try:
    N = int(sys.argv[1])
    algo = sys.argv[2].upper()
except ValueError:
    print("Lỗi: Tham số thứ nhất phải là một số nguyên")
    sys.exit(1)

# Xóa file output cũ nếu có
if os.path.exists('output.txt'):
    os.remove('output.txt')

# Đọc cấu hình vùng
with open('Sudoku_Regions.txt') as f:
    content = f.read()
dict_construct = 'regions_dict = {' + content + '}'
regions_dict = {}
exec(dict_construct)
numbers_set = set(range(1, N + 1))

def construct_sudoku_array():
    with open('Sudoku.txt') as f:
        file_content = list(filter((lambda x: x != ',' and x != '\n'), list(f.read())))
    sudoku_array = np.array(file_content, dtype=int).reshape(N, N)
    return sudoku_array

# Tạo bản đồ vùng cực nhanh
region_map = np.zeros((N, N), dtype=object)
for r_id, points in regions_dict.items():
    for (r, c) in points:
        region_map[r, c] = r_id

def find_region_fast(i, j):
    return region_map[i, j]

def find_region(i, j):
    for v, d in regions_dict.items():
        if (i, j) in d:
            return v

# ==========================================
# CÁC HÀM XỬ LÝ LOGIC CHUNG
# ==========================================
def find_regional_numbers_set(x, i, j):
    regional_points = regions_dict[find_region_fast(i, j)]
    regional_points_set = set(x[a] for a in regional_points)
    return regional_points_set

def find_available_numbers(x, i, j):
    set_1 = set(x[i, :])
    set_2 = set(x[:, j])
    set_3 = find_regional_numbers_set(x, i, j)
    return numbers_set.difference(set_1.union(set_2.union(set_3)))

def find_empty(x):
    """
    Tối ưu hóa: Tìm ô trống dựa trên Heuristic MRV (Minimum Remaining Values)
    Cắt nhánh sớm nếu có ô chỉ còn <= 1 lựa chọn.
    """
    min_options = N + 1
    best_cell = None
    for i in range(N):
        for j in range(N):
            if x[i, j] == 0:
                options = len(find_available_numbers(x, i, j))
                if options <= 1:
                    return (i, j) # Cắt nhánh sớm
                if options < min_options:
                    min_options = options
                    best_cell = (i, j)
    return best_cell

def is_valid(sudoku, row, col):
    val = sudoku[row][col]
    if np.count_nonzero(sudoku[row, :] == val) > 1: return False
    if np.count_nonzero(sudoku[:, col] == val) > 1: return False
    region = regions_dict[find_region_fast(row, col)]
    return np.count_nonzero([sudoku[i,j] == val for (i,j) in region]) <= 1

# ==========================================
# THUẬT TOÁN DFS (TỐI ƯU MRV)
# ==========================================
def solve(sudoku_array, state_count=0, states=None):
    if states is None:
        states = []

    empty_index = find_empty(sudoku_array)
    if not empty_index:
        return True, state_count, states
    
    row, col = empty_index
    available_numbers = find_available_numbers(sudoku_array, row, col)

    if len(available_numbers) == 0:
        return False, state_count, states

    for x in available_numbers:
        sudoku_array[row, col] = x
        states.append(sudoku_array.copy()) # Lưu trạng thái cho Playback
        state_count += 1
        
        solved, state_count, states = solve(sudoku_array, state_count, states)
        if solved:
            return True, state_count, states
            
        sudoku_array[row, col] = 0 # Quay lui

    return False, state_count, states

def solve_with_metrics(sudoku_array):
    state_count = 0
    states = [sudoku_array.copy()]
    
    tracemalloc.start()
    start_time = time.time()
    
    solved, state_count, states = solve(sudoku_array, state_count, states)
    
    end_time = time.time()
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    with open('output.txt', 'a') as f:
        f.write(f"DFS Algorithm:\nStates: {state_count}\nTime: {end_time - start_time:.2f} seconds\nMemory: {peak_memory / 1024:.2f} KB\n\n")
        
    if solved:
        return sudoku_array, states
    else:
        return None, states

# ==========================================
# THUẬT TOÁN A* TỐI ƯU
# ==========================================
def calculate_heuristic(sudoku):
    h = 0
    empty_cells = 0
    available_cache = {}
    
    for i in range(N):
        for j in range(N):
            if sudoku[i, j] == 0:
                empty_cells += 1
                if (i,j) not in available_cache:
                    available_cache[(i,j)] = find_available_numbers(sudoku, i, j)
                available = available_cache[(i,j)]
                
                if not available:
                    h += N * 2  
                else:
                    h += 2.0 / len(available)  
                    
    region_penalties = 0
    for region in regions_dict.values():
        region_vals = [sudoku[i,j] for i,j in region if sudoku[i,j] != 0]
        if len(region_vals) != len(set(region_vals)):
            region_penalties += N
            
    return h + empty_cells + region_penalties

def lcv_heuristic(sudoku, row, col, num):
    conflict_count = 0
    region = regions_dict[find_region_fast(row, col)]
    for (i, j) in region:
        if sudoku[i][j] == 0 and num in find_available_numbers(sudoku, i, j):
            conflict_count += 1
    return conflict_count

def a_star_optimized(initial):
    open_heap = []
    closed = set()
    sequence = 0
    state_count = 0
    states = [initial.copy()]
    
    tracemalloc.start()
    start_time = time.time()
    
    initial_cost = calculate_heuristic(initial)
    heapq.heappush(open_heap, (initial_cost, sequence, initial.copy()))
    
    while open_heap:
        current_cost, _, current = heapq.heappop(open_heap)
        current_bytes = current.tobytes()
        
        if current_bytes in closed:
            continue
        closed.add(current_bytes)
        state_count += 1
        
        empty = find_empty(current)
        if not empty:
            end_time = time.time()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            with open('output.txt', 'a') as f:
                f.write(f"A* Optimized Algorithm:\nStates: {state_count}\n"
                       f"Time: {end_time - start_time:.2f}s\n"
                       f"Memory: {peak_memory/1024:.2f} KB\n\n")
            return current, states
        
        row, col = empty
        available_numbers = find_available_numbers(current, row, col)
        lcv_sorted = sorted(available_numbers, key=lambda num: lcv_heuristic(current, row, col, num))
        
        for num in lcv_sorted:
            new_state = current.copy()
            new_state[row, col] = num
            
            if is_valid(new_state, row, col):
                new_h = calculate_heuristic(new_state)
                states.append(new_state.copy()) # Lưu trạng thái cho Playback
                heapq.heappush(open_heap, (new_h, sequence, new_state))
                sequence += 1
                
    tracemalloc.stop()
    return None, states

# ==========================================
# GIAO DIỆN & PLAYBACK (UI)
# ==========================================
recorded_states = []
current_step = 0

def generate_colors(num_colors):
    pastel_colors = [
        '#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF',
        '#E8BAFF', '#E2F0CB', '#FFC8A2', '#D5AAFF', '#B5EAD7'
    ]
    return [pastel_colors[i % len(pastel_colors)] for i in range(num_colors)]

region_colors = generate_colors(len(regions_dict))
region_indices = {region: idx for idx, region in enumerate(regions_dict.keys())}

def display_sudoku(sudoku):
    for i in range(N):
        for j in range(N):
            region = find_region_fast(i, j)
            entries[i][j].delete(0, tk.END)
            entries[i][j].config(bg=region_colors[region_indices[region]], fg="#2C3E50")
            if sudoku[i, j] != 0:
                entries[i][j].insert(0, str(sudoku[i, j]))

def show_step():
    global recorded_states, current_step
    if not recorded_states: return
    display_sudoku(recorded_states[current_step])
    step_label.config(text=f"Bước: {current_step + 1} / {len(recorded_states)}")

def step_forward():
    global current_step
    if current_step < len(recorded_states) - 1:
        current_step += 1
        show_step()

def step_backward():
    global current_step
    if current_step > 0:
        current_step -= 1
        show_step()

def solve_sudoku():
    global recorded_states, current_step
    sudoku = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            value = entries[i][j].get()
            if value:
                sudoku[i, j] = int(value)
                
    step_label.config(text="AI đang suy nghĩ...")
    root.update()

    if algo == "A":
        solved_sudoku, states = a_star_optimized(sudoku)
    elif algo == "B":
        solved_sudoku, states = solve_with_metrics(sudoku)
    else:
        print("Lỗi: Tham số thứ hai phải là 'A' hoặc 'B'")
        sys.exit(1)

    recorded_states = states
    
    if recorded_states:
        current_step = len(recorded_states) - 1 
        show_step()
        prev_btn.config(state=tk.NORMAL)
        next_btn.config(state=tk.NORMAL)
        
    if solved_sudoku is None:
        messagebox.showinfo("Kết quả", "Không tìm thấy lời giải cho bài toán này!")

def check_solution():
    sudoku = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            value = entries[i][j].get()
            if value: sudoku[i, j] = int(value)
    
    for i in range(N):
        if len(set(sudoku[i, :])) != N:
            messagebox.showerror("Kết quả", "Sai luật trên Hàng!")
            return
    for j in range(N):
        if len(set(sudoku[:, j])) != N:
            messagebox.showerror("Kết quả", "Sai luật trên Cột!")
            return
    for region in regions_dict.values():
        region_values = [sudoku[i, j] for i, j in region]
        if len(set(region_values)) != N:
            messagebox.showerror("Kết quả", "Sai luật trong Vùng (Region)!")
            return
            
    messagebox.showinfo("Kết quả", "Tuyệt vời! Giải pháp chính xác.")

def reset_sudoku():
    global recorded_states, current_step
    recorded_states = []
    current_step = 0
    step_label.config(text="Sẵn sàng")
    prev_btn.config(state=tk.DISABLED)
    next_btn.config(state=tk.DISABLED)
    sudoku = construct_sudoku_array()
    display_sudoku(sudoku)

# ==========================================
# KHỞI TẠO CỬA SỔ CHÍNH
# ==========================================
root = tk.Tk()
root.title("Jigsaw Sudoku AI Solver")
root.config(bg="#F4F6F7")

window_width = N * 80
window_height = N * 80 + 220
root.geometry(f"{window_width}x{window_height}")
root.resizable(False, False)

title_label = tk.Label(root, text="JIGSAW SUDOKU", font=('Helvetica', 24, 'bold'), bg="#F4F6F7", fg="#2C3E50")
title_label.pack(pady=(15, 5))

frame = tk.Frame(root, bg="#34495E", bd=2)
frame.pack(pady=5)

entries = [[None for _ in range(N)] for _ in range(N)]
for i in range(N):
    for j in range(N):
        entries[i][j] = tk.Entry(
            frame, width=3, font=('Helvetica', 24, 'bold'), 
            justify='center', borderwidth=1, relief="solid", 
            cursor="hand2"
        )
        entries[i][j].grid(row=i, column=j, ipadx=5, ipady=15, padx=1, pady=1)

# --- THANH CÔNG CỤ CHÍNH ---
button_frame = tk.Frame(root, bg="#F4F6F7")
button_frame.pack(pady=10)

btn_font = ('Helvetica', 11, 'bold')
solve_button = tk.Button(button_frame, text="🚀 SOLVE", command=solve_sudoku, font=btn_font, bg="#27AE60", fg="white", relief="flat", width=10, cursor="hand2")
solve_button.pack(side=tk.LEFT, padx=5)

check_button = tk.Button(button_frame, text="✔️ CHECK", command=check_solution, font=btn_font, bg="#E67E22", fg="white", relief="flat", width=10, cursor="hand2")
check_button.pack(side=tk.LEFT, padx=5)

reset_button = tk.Button(button_frame, text="🔄 RESET", command=reset_sudoku, font=btn_font, bg="#2980B9", fg="white", relief="flat", width=10, cursor="hand2")
reset_button.pack(side=tk.LEFT, padx=5)

# --- THANH ĐIỀU KHIỂN PLAYBACK ---
playback_frame = tk.Frame(root, bg="#ecf0f1", bd=1, relief="solid")
playback_frame.pack(pady=5, padx=20, fill=tk.X)

prev_btn = tk.Button(playback_frame, text="⏪ Lùi", command=step_backward, font=btn_font, bg="#95a5a6", fg="white", relief="flat", width=8, state=tk.DISABLED, cursor="hand2")
prev_btn.pack(side=tk.LEFT, padx=10, pady=5)

step_label = tk.Label(playback_frame, text="Sẵn sàng", font=('Helvetica', 12, 'bold'), bg="#ecf0f1", fg="#2c3e50")
step_label.pack(side=tk.LEFT, expand=True, pady=5)

next_btn = tk.Button(playback_frame, text="Tiến ⏩", command=step_forward, font=btn_font, bg="#95a5a6", fg="white", relief="flat", width=8, state=tk.DISABLED, cursor="hand2")
next_btn.pack(side=tk.RIGHT, padx=10, pady=5)

# Load dữ liệu ban đầu
sudoku = construct_sudoku_array()
display_sudoku(sudoku)

root.mainloop()