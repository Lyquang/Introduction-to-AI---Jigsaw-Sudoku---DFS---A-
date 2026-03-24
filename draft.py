import numpy as np
import tkinter as tk
from tkinter import messagebox
import time
import heapq
import tracemalloc
import os
import random
import sys

# Định nghĩa kích thước của bài toán
if len(sys.argv) != 2:
    print("Cách dùng: python script.py <N>")
    sys.exit(1)

try:
    N = int(sys.argv[1])

except ValueError:
    print("Lỗi: Kích thước N phải là một số nguyên")
    sys.exit(1)

#Delete the output file if it exists
if os.path.exists('output.txt'):
    os.remove('output.txt')

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

def find_empty(x):
# Tìm tất cả các ô trống và chọn ô có số lượng giá trị khả dụng ít nhất để tăng hiệu quả của thuật toán
    empty_items_list = []
    for index, item in np.ndenumerate(x):
        if item == 0:
            empty_items_list.append(index)
    if len(empty_items_list) != 0:
        empty_items_num_of_available_numbers = []
        for i in empty_items_list:
            a = len(find_available_numbers(x, i[0], i[1]))
            empty_items_num_of_available_numbers.append(a)
            #trả về ô trống có số lượng giá trị khả dụng ít nhất
        return empty_items_list[empty_items_num_of_available_numbers.index(min(empty_items_num_of_available_numbers))]
    return None

def find_region(i, j):
    # Tìm vùng của ô (i, j) bằng cách duyệt qua dictionary regions_dict
    for v, d in regions_dict.items():
        if (i, j) in d:
            return v
        
# Tạo bản đồ vùng ngay sau khi đọc regions_dict
region_map = np.zeros((N, N), dtype=object)
for r_id, points in regions_dict.items():
    for (r, c) in points:
        region_map[r, c] = r_id

# Hàm mới cực nhanh
def find_region_fast(i, j):
    return region_map[i, j]

# Tìm tập hợp các số đã xuất hiện trong hàng, cột và vùng của ô (i, j) để xác định các số khả dụng
def find_regional_numbers_set(x, i, j):
    # Tìm tập hợp các số đã xuất hiện trong vùng của ô (i, j)
    regional_points = regions_dict[find_region_fast(i, j)]
    # Tạo một tập hợp chứa các số đã xuất hiện trong vùng bằng cách lấy giá trị của các ô trong vùng đó
    regional_points_set = set(x[a] for a in regional_points)
    # Trả về tập hợp các số đã xuất hiện trong vùng
    return regional_points_set

def find_available_numbers(x, i, j):
    # Tìm tập hợp các số đã xuất hiện trong hàng, cột và vùng của ô (i, j)
    set_1 = set(x[i, :])
    # Tìm tập hợp các số đã xuất hiện trong cột của ô (i, j)
    set_2 = set(x[:, j])
    # Tìm tập hợp các số đã xuất hiện trong vùng của ô (i, j)
    set_3 = find_regional_numbers_set(x, i, j)
    # Trả về tập hợp các số khả dụng bằng cách lấy hiệu của tập numbers_set với hợp của các tập đã xuất hiện
    return numbers_set.difference(set_1.union(set_2.union(set_3)))


def solve(sudoku_array, state_count=0, states=[]):
    # BƯỚC 1: Chọn ô để giải. Hàm find_empty chọn ô có ít lựa chọn nhất (MRV)
    empty_index = find_empty(sudoku_array)
    print(f"[*] Tìm ô trống: {empty_index}")
    
    if not empty_index:
        print("=> THÀNH CÔNG: Không còn ô trống, đã tìm ra lời giải!")
        return True, state_count, states
    
    row, col = empty_index
    # BƯỚC 2: Tính toán danh sách các số phù hợp (không vi phạm hàng, cột, vùng)
    available_numbers = find_available_numbers(sudoku_array, row, col)
    
    print(f"[*] Đang xét ô ({row}, {col}): Danh sách số phù hợp là {list(available_numbers)}")

    # Nếu ô hiện tại không có số nào phù hợp (tập rỗng)
    if len(available_numbers) == 0:
        print(f" [!] CỤT ĐƯỜNG: Ô ({row}, {col}) không có số phù hợp. Sẽ quay lui!")
        return False, state_count, states

    # BƯỚC 3: Thử từng số trong danh sách phù hợp
    for x in available_numbers:
        print(f"  (+) Thử đặt số {x} vào ô ({row}, {col})")
        sudoku_array[empty_index] = x
        
        # Cập nhật giao diện Tkinter
        display_sudoku(sudoku_array)
        root.update()
        
        states.append(sudoku_array.copy())
        state_count += 1
        
        # BƯỚC 4: Đệ quy để giải ô tiếp theo
        solved, state_count, states = solve(sudoku_array, state_count, states)
        
        if solved:
            return True, state_count, states
        
        # BƯỚC 5: QUAY LUI (BACKTRACK)
        # Nếu nhánh phía sau trả về False, dòng code dưới đây sẽ thực thi
        print(f"  (-) Số {x} tại ({row}, {col}) dẫn đến sai lầm. Đang xoá số {x}, quay lại thử số khác...")
        sudoku_array[empty_index] = 0
        display_sudoku(sudoku_array)
        root.update()
    
    return False, state_count, states


def solve_with_metrics(sudoku_array):
    state_count = 0
    states = []
    tracemalloc.start()
    start_time = time.time()
    solved, state_count, states = solve(sudoku_array, state_count, states)
    end_time = time.time()
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    with open('output.txt', 'a') as f:
        f.write(f"DFS Algorithm:\nStates: {state_count}\nTime: {end_time - start_time:.2f} seconds\nMemory: {peak_memory / 1024:.2f} KB\n\n")
        for state in states:
            f.write(np.array2string(state) + "\n\n")
    if solved:
        return sudoku_array
    else:
        return None

def calculate_heuristic(sudoku):
    """Heuristic tổng hợp cho Jigsaw Sudoku"""
    h = 0
    empty_cells = 0
    conflict_penalty = 0
    
    for i in range(N):
        for j in range(N):
            if sudoku[i, j] == 0:
                empty_cells += 1
                available = find_available_numbers(sudoku, i, j)
                if not available:
                    h += N * 2  
                else:
                    h += 1.0 / len(available)  
    
    #Check for conflicts in regions
    for region in regions_dict.values():
        values = [sudoku[i,j] for (i,j) in region if sudoku[i,j] != 0]
        conflict_penalty += (len(values) - len(set(values))) * N
        
    return h + empty_cells + conflict_penalty

def a_star_optimized(initial):
    open_heap = []
    closed = set()
    sequence = 0
    state_count = 0
    states = []
    
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
                for state in states:
                    f.write(np.array2string(state) + "\n\n")
            return current
        
        row, col = empty
        available_numbers = find_available_numbers(current, row, col)
        
        # Sort available numbers by least constraining value heuristic
        lcv_sorted = sorted(available_numbers, 
                          key=lambda num: lcv_heuristic(current, row, col, num))
        
        for num in lcv_sorted:
            new_state = current.copy()
            new_state[row, col] = num
            
            if is_valid(new_state, row, col):
                new_h = calculate_heuristic(new_state)
                new_cost = new_h
                
                display_sudoku(new_state)
                root.update()
                states.append(new_state.copy())
                
                heapq.heappush(open_heap, (new_cost, sequence, new_state))
                sequence += 1
    
    tracemalloc.stop()
    return None

def lcv_heuristic(sudoku, row, col, num):
    """Heuristic cho Least Constraining Value"""
    conflict_count = 0
    region = regions_dict[find_region(row, col)]
    for (i, j) in region:
        if sudoku[i][j] == 0 and num in find_available_numbers(sudoku, i, j):
            conflict_count += 1
    return conflict_count

def is_valid(sudoku, row, col):
    """Kiểm tra tính hợp lệ của giá trị mới trong ô"""
    val = sudoku[row][col]
    # Check hàng
    if np.count_nonzero(sudoku[row, :] == val) > 1:
        return False
    # Check cột
    if np.count_nonzero(sudoku[:, col] == val) > 1:
        return False
    # Check vùng
    region = regions_dict[find_region(row, col)]
    return np.count_nonzero([sudoku[i,j] == val for (i,j) in region]) <= 1

def generate_colors(num_colors):
    """Generate a list of distinct colors."""
    colors = []
    for i in range(num_colors):
        color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        colors.append(color)
    return colors

# Define colors for each region
region_colors = generate_colors(len(regions_dict))

# Map region names to indices
region_indices = {region: idx for idx, region in enumerate(regions_dict.keys())}

def display_sudoku(sudoku):
    for i in range(N):
        for j in range(N):
            region = find_region(i, j)
            entries[i][j].delete(0, tk.END)
            entries[i][j].config(bg=region_colors[region_indices[region]])
            if sudoku[i, j] != 0:
                entries[i][j].insert(0, str(sudoku[i, j]))

def solve_sudoku():
    sudoku = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            value = entries[i][j].get()
            if value:
                sudoku[i, j] = int(value)
    if algo == "A":
        solved_sudoku = a_star_optimized(sudoku)
    elif algo == "B":
        solved_sudoku = solve_with_metrics(sudoku)
    else:
        print("Lỗi: Tham số thứ hai phải là 'A' hoặc 'B'")
        sys.exit(1)

    if solved_sudoku is not None:
        display_sudoku(solved_sudoku)
    else:
        messagebox.showinfo("Sudoku Solver", "No solution exists")

def check_solution():
    sudoku = np.zeros((N, N), dtype=int)
    for i in range(N):
        for j in range(N):
            value = entries[i][j].get()
            if value:
                sudoku[i, j] = int(value)
    
    for i in range(N):
        if len(set(sudoku[i, :])) != N:
            messagebox.showinfo("Sudoku Solver", "Incorrect solution")
            return
    
    for j in range(N):
        if len(set(sudoku[:, j])) != N:
            messagebox.showinfo("Sudoku Solver", "Incorrect solution")
            return
    
    for region in regions_dict.values():
        region_values = [sudoku[i, j] for i, j in region]
        if len(set(region_values)) != N:
            messagebox.showinfo("Sudoku Solver", "Incorrect solution")
            return
    
    messagebox.showinfo("Sudoku Solver", "Correct solution")

sudoku = construct_sudoku_array()

def reset_sudoku():
    sudoku = construct_sudoku_array()
    display_sudoku(sudoku)

root = tk.Tk()
root.title("Sudoku Solver")

root.geometry(f"{N*80}x{N*110}")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(pady=10)

entries = [[None for _ in range(N)] for _ in range(N)]
for i in range(N):
    for j in range(N):
        entries[i][j] = tk.Entry(frame, width=4, font=('Arial', 22, 'bold'), justify='center', borderwidth=2, relief="solid")
        entries[i][j].grid(row=i, column=j, ipadx=1, ipady=15, padx=3, pady=3)

button_frame = tk.Frame(root)
button_frame.pack(pady=10)

solve_button = tk.Button(button_frame, text="Solve", command=solve_sudoku, font=('Arial', 14), bg="#4CAF50", fg="white", relief="raised", width=15)
solve_button.pack(side=tk.LEFT, padx=5)

check_button = tk.Button(button_frame, text="Check Solution", command=check_solution, font=('Arial', 14), bg="#FF5733", fg="white", relief="raised", width=15)
check_button.pack(side=tk.LEFT, padx=5)

reset_frame = tk.Frame(root)
reset_frame.pack(pady=10)

reset_button = tk.Button(reset_frame, text="Reset", command=reset_sudoku, font=('Arial', 14), bg="#2196F3", fg="white", relief="raised", width=15)
reset_button.pack()

display_sudoku(sudoku)

root.mainloop()

def calculate_heuristic(sudoku):
    """Heuristic tổng hợp với trọng số cho các yếu tố khác nhau"""
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

