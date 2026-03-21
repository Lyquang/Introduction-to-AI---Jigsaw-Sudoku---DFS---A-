import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import heapq
import tracemalloc
import os
import random
import sys
import ast

# ----------------- THIẾT LẬP KÍCH THƯỚC BÀI TOÁN -----------------
if len(sys.argv) != 2:
    print("Cách dùng: python main.py <N>")
    sys.exit(1)

try:
    N = int(sys.argv[1])
except ValueError:
    print("Lỗi: Tham số N phải là một số nguyên")
    sys.exit(1)

# Xóa file output cũ nếu tồn tại để ghi số liệu mới
if os.path.exists('output.txt'):
    os.remove('output.txt')

# Tập hợp các số hợp lệ từ 1 đến N
NUMBERS_SET = set(range(1, N + 1))

# ----------------- ĐỌC DỮ LIỆU ĐẦU VÀO -----------------
def load_regions(filepath):
    """Đọc file Sudoku_Regions và chuyển thành Dictionary an toàn"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.endswith(','): 
                content = content[:-1] # Loại bỏ dấu phẩy thừa ở cuối nếu có
            return ast.literal_eval('{' + content + '}')
    except Exception as e:
        print(f"Lỗi đọc file regions: {e}")
        sys.exit(1)

regions_dict = load_regions('Sudoku_Regions.txt')

def construct_sudoku_array():
    """Đọc ma trận Sudoku khởi đầu từ file"""
    try:
        with open('Sudoku.txt', 'r', encoding='utf-8') as f:
            file_content = [char for char in f.read() if char.isdigit()]
        return np.array(file_content, dtype=int).reshape(N, N)
    except Exception as e:
        print(f"Lỗi đọc file Sudoku khởi tạo: {e}")
        sys.exit(1)

# ----------------- CÁC HÀM XỬ LÝ RÀNG BUỘC SUDOKU -----------------
def find_region(i, j):
    """Tìm xem tọa độ (i,j) thuộc region nào"""
    for region_name, coords in regions_dict.items():
        if (i, j) in coords:
            return region_name
    return None

def find_available_numbers(sudoku, i, j):
    """Tìm các con số hợp lệ có thể điền vào ô (i, j)"""
    # Lấy các số đã có trên hàng i và cột j
    set_row = set(sudoku[i, :])
    set_col = set(sudoku[:, j])
    
    # Lấy các số đã có trong vùng (region) chứa ô (i,j)
    region_name = find_region(i, j)
    set_region = set(sudoku[r, c] for r, c in regions_dict[region_name])
    
    # Số hợp lệ = Tập các số {1..N} trừ đi các số đã xuất hiện
    used_numbers = set_row.union(set_col).union(set_region)
    return NUMBERS_SET.difference(used_numbers)

def find_best_empty_cell(sudoku):
    """
    Heuristic MRV (Minimum Remaining Values): 
    Tìm ô trống có ÍT lựa chọn hợp lệ nhất để xét trước.
    Trả về: tọa độ (i, j) và danh sách các số hợp lệ của ô đó.
    """
    min_options = float('inf')
    best_cell = None
    best_available = set()
    
    for i in range(N):
        for j in range(N):
            if sudoku[i, j] == 0:
                available = find_available_numbers(sudoku, i, j)
                num_options = len(available)
                
                # Nếu có 1 ô trống không có số nào hợp lệ -> Trạng thái này vô nghiệm (Dead end)
                if num_options == 0:
                    return (i, j), set()
                
                if num_options < min_options:
                    min_options = num_options
                    best_cell = (i, j)
                    best_available = available
                    
                    # Tối ưu: Nếu tìm thấy ô chỉ có 1 lựa chọn duy nhất thì chọn luôn
                    if min_options == 1:
                        return best_cell, best_available
                        
    return best_cell, best_available

def calculate_heuristic(sudoku):
    """
    Hàm tính giá trị Heuristic (h) cho thuật toán A*.
    h = Tổng số ô trống còn lại + tổng penalty_value của từng ô trống. 
    penalty_value: 
        Nếu ô trống còn lại không còn lựa chọn hợp lệ => gán penalty_value của ô trống này với giá trị lớn (N * 100) => Những state này ở cuối hàng đợi, tránh để giải thuật lặp qua
    """
    h = 0
    empty_cells = 0
    conflict_penalty = 0
    for i in range(N):
        for j in range(N):
            if sudoku[i, j] == 0:
                empty_cells += 1
                available = find_available_numbers(sudoku, i, j)
                if not available:
                    h += N * 100 
    
    #Check for conflicts in regions
    for region in regions_dict.values():
        values = [sudoku[i,j] for (i,j) in region if sudoku[i,j] != 0]
        conflict_penalty += (len(values) - len(set(values))) * N
    return h + empty_cells + conflict_penalty
def find_regional_numbers_set(x, i, j):
    regional_points = regions_dict[find_region(i, j)]
    regional_points_set = set(x[a] for a in regional_points)
    return regional_points_set
def find_available_numbers(x, i, j):
    set_1 = set(x[i, :])
    set_2 = set(x[:, j])
    set_3 = find_regional_numbers_set(x, i, j)
    return NUMBERS_SET.difference(set_1.union(set_2.union(set_3)))
def lcv_heuristic(sudoku, row, col, num):
    """Heuristic cho Least Constraining Value"""
    conflict_count = 0
    region = regions_dict[find_region(row, col)]
    for (i, j) in region:
        if sudoku[i][j] == 0 and num in find_available_numbers(sudoku, i, j):
            conflict_count += 1
    return conflict_count
# ----------------- THUẬT TOÁN A* TỐI ƯU -----------------
def a_star_solver(initial_state):
    """
    Giải thuật A* sử dụng Priority Queue.
    Priority Queue lưu trữ tuple: (f_cost, sequence, state)
    f_cost: Là giá trị heuristic của state
    sequence: 
        giá trị này để tránh trường hợp lỗi khi f_cost của hai state bằng nhau (lỗi khi so sánh 2 state)
        và để tạo ra một cơ chế xử lí trường hợp f_cost bằng nhau => state nào được push vào queue trước thì xử lí trước
    Trong đó f_cost = g (số ô đã điền) + h (heuristic đánh giá)
    """
    open_heap = []
    closed_set = set() # Dùng để tránh duyệt lại các trạng thái trùng lặp
    sequence = 0 # Biến đếm dùng để so sánh các trạng thái có cùng f_cost trong heapq
    state_count = 0
    
    tracemalloc.start()
    start_time = time.time()
    
    # Heuristic trạng thái ban đầu
    initial_h = calculate_heuristic(initial_state)
    heapq.heappush(open_heap, (initial_h, sequence, initial_state.copy()))
    
    while open_heap:
        current_f, _, current_state = heapq.heappop(open_heap)
        
        # Hash ma trận thành byte để lưu vào closed_set (bảo vệ bộ nhớ)
        state_bytes = current_state.tobytes()
        if state_bytes in closed_set:
            continue
        closed_set.add(state_bytes)
        state_count += 1
        
        # Áp dụng MRV để tìm ô trống tiếp theo tốt nhất
        best_cell, available_numbers = find_best_empty_cell(current_state)
        
        # Nếu không còn ô trống nào -> Đã tìm ra lời giải!
        if not best_cell:
            end_time = time.time()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Ghi báo cáo số liệu
            with open('output.txt', 'a', encoding='utf-8') as f:
                f.write(f"--- BÁO CÁO THUẬT TOÁN A* ---\n")
                f.write(f"Số trạng thái đã sinh: {state_count}\n")
                f.write(f"Thời gian chạy: {end_time - start_time:.4f} giây\n")
                f.write(f"Tiêu tốn bộ nhớ (Peak): {peak_memory / 1024:.2f} KB\n\n")
                f.write(np.array2string(current_state) + "\n")
            
            return current_state
        row, col = best_cell
        # Trong các giá trị hợp lệ, ưu tiên xét trước những giá trị mà giá trị này là giá trị hợp lệ của ít ô trống nhất trong region
        lcv_sorted = sorted(available_numbers, 
                          key=lambda num: lcv_heuristic(current_state, row, col, num))
        
        # Sinh các trạng thái con theo thứ tự ưu tiên trên
        
        for num in lcv_sorted:
            new_state = current_state.copy()
            new_state[row, col] = num
            
            # Hàm f(n) 
            f_cost = calculate_heuristic(new_state)
            
            sequence += 1
            heapq.heappush(open_heap, (f_cost, sequence, new_state))
            
            # Cập nhật GUI 
            display_sudoku(new_state)
            root.update()
            
    tracemalloc.stop()
    return None # Vô nghiệm

# ----------------- GIAO DIỆN TKINTER (GUI) -----------------
def generate_colors(num_colors):
    """Tạo màu ngẫu nhiên cho các vùng Region"""
    colors = []
    for _ in range(num_colors):
        color = "#{:02x}{:02x}{:02x}".format(random.randint(150, 255), 
                                             random.randint(150, 255), 
                                             random.randint(150, 255)) # Dùng màu sáng cho dễ nhìn text
        colors.append(color)
    return colors

# Gán màu cố định cho các region để giao diện không bị giật màu khi update
region_colors = generate_colors(len(regions_dict))
region_indices = {region: idx for idx, region in enumerate(regions_dict.keys())}

def display_sudoku(sudoku):
    """Cập nhật ma trận lên giao diện UI"""
    for i in range(N):
        for j in range(N):
            region = find_region(i, j)
            entries[i][j].delete(0, tk.END)
            entries[i][j].config(bg=region_colors[region_indices[region]])
            if sudoku[i, j] != 0:
                entries[i][j].insert(0, str(sudoku[i, j]))

def gui_solve():
    """Hàm kích hoạt khi bấm nút Solve"""
    # Lấy state hiện tại từ GUI (nếu người dùng nhập thêm)
    current_sudoku = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            val = entries[i][j].get()
            if val.isdigit():
                current_sudoku[i, j] = int(val)
                
    solved_sudoku = a_star_solver(current_sudoku)
    
    if solved_sudoku is not None:
        display_sudoku(solved_sudoku)
        messagebox.showinfo("Sudoku Solver", "Giải thành công! Số liệu đã được lưu vào output.txt")
    else:
        messagebox.showwarning("Sudoku Solver", "Bài toán vô nghiệm!")

def gui_reset():
    """Reset lại trạng thái ban đầu"""
    initial_sudoku = construct_sudoku_array()
    display_sudoku(initial_sudoku)

# Khởi tạo cửa sổ chính
root = tk.Tk()
root.title("Jigsaw Sudoku - A* Algorithm Solver")
root.geometry(f"{N*80 + 50}x{N*90 + 100}")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(pady=10)

# Khởi tạo lưới ô nhập
entries = [[None for _ in range(N)] for _ in range(N)]
for i in range(N):
    for j in range(N):
        entries[i][j] = tk.Entry(frame, width=3, font=('Arial', 24, 'bold'), 
                                 justify='center', borderwidth=2, relief="solid")
        entries[i][j].grid(row=i, column=j, ipadx=5, ipady=15, padx=2, pady=2)

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

solve_btn = tk.Button(button_frame, text="Solve (A*)", command=gui_solve, font=('Arial', 14, 'bold'), bg="#4CAF50", fg="white", width=12)
solve_btn.pack(side=tk.LEFT, padx=10)

reset_btn = tk.Button(button_frame, text="Reset", command=gui_reset, font=('Arial', 14, 'bold'), bg="#F44336", fg="white", width=12)
reset_btn.pack(side=tk.LEFT, padx=10)

# Load và hiển thị trạng thái đầu tiên
initial_sudoku = construct_sudoku_array()
display_sudoku(initial_sudoku)

root.mainloop()